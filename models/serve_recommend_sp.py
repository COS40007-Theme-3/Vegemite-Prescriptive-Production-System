"""
Python backend for serve_recommend_sp — v2 (improved).

Improvements over v1:
- Accepts all 7 SP columns + 'part' (yeast type) in JSON input
- Routes to per-Part sub-models (vegemite_task1_per_part.joblib) when available
- Joint SP optimization: grid search over all 7 SPs simultaneously
- Correct SP column mapping (no more mislabeled extractTankSP)
- Rolling features computed at inference time (window=3)

Protocol:
- Read a single line of JSON from stdin:
  {
    "ffteFeedSolidsSP": number,       -> FFTE Feed solids SP
    "ffteProductionSolidsSP": number, -> FFTE Production solids SP
    "ffteSteamPressureSP": number,    -> FFTE Steam pressure SP
    "tfeOutFlowSP": number,           -> TFE Out flow SP
    "tfeProductionSolidsSP": number,  -> TFE Production solids SP
    "tfeVacuumPressureSP": number,    -> TFE Vacuum pressure SP
    "tfeSteamPressureSP": number,     -> TFE Steam pressure SP
    "part": string                    -> e.g. "Yeast - BRD"
  }
- Write a single line of JSON to stdout:
  {
    "recommendedSP": { all 7 SP keys },
    "pGood": float,
    "pDowntime": float,
    "prediction": "GOOD" | "LOW_BAD" | "HIGH_BAD",
    "downtimeRisk": float,
    "recommendedPGood": float,
    "recommendedPDowntime": float
  }
"""

import itertools
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score
from sklearn.utils.class_weight import compute_class_weight

try:
    import xgboost as xgb  # type: ignore
except Exception as e:
    print(json.dumps({"error": f"xgboost not available: {e}"}))
    sys.exit(1)

try:
    import joblib  # type: ignore
except Exception as e:
    joblib = None

try:
    from imblearn.over_sampling import SMOTE  # type: ignore
    _HAS_SMOTE = True
except ImportError:
    _HAS_SMOTE = False

try:
    from sklearn.calibration import CalibratedClassifierCV
    _HAS_CALIBRATION = True
except ImportError:
    _HAS_CALIBRATION = False


BASE_DIR = Path(__file__).resolve().parents[1]
THEME3_ROOT = BASE_DIR / "data" / "Theme3"
DATA_MAIN = THEME3_ROOT / "data_02_07_2019-26-06-2020"
DATA_DOWNTIME = THEME3_ROOT / "Downtime"
MODELS_DIR = BASE_DIR / "models"

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Joblib model paths
TASK1_MODEL_PATH = MODELS_DIR / "vegemite_task1.joblib"
TASK1_PER_PART_PATH = MODELS_DIR / "vegemite_task1_per_part.joblib"
TASK2_MODEL_PATH = MODELS_DIR / "vegemite_task2.joblib"
ARTIFACTS_PATH = MODELS_DIR / "vegemite_artifacts.joblib"

# Canonical SP column names (all 7)
ALL_SP_COLS = [
    "FFTE Feed solids SP",
    "FFTE Production solids SP",
    "FFTE Steam pressure SP",
    "TFE Out flow SP",
    "TFE Production solids SP",
    "TFE Vacuum pressure SP",
    "TFE Steam pressure SP",
]

# UI key → canonical column name mapping (all 7, correctly labeled)
UI_TO_SP = {
    "ffteFeedSolidsSP":       "FFTE Feed solids SP",
    "ffteProductionSolidsSP": "FFTE Production solids SP",
    "ffteSteamPressureSP":    "FFTE Steam pressure SP",
    "tfeOutFlowSP":           "TFE Out flow SP",
    "tfeProductionSolidsSP":  "TFE Production solids SP",
    "tfeVacuumPressureSP":    "TFE Vacuum pressure SP",
    "tfeSteamPressureSP":     "TFE Steam pressure SP",
}

# Reverse: canonical → UI key
SP_TO_UI = {v: k for k, v in UI_TO_SP.items()}


def _find_file(folder: Path, names: list) -> Path:
    for n in names:
        p = folder / n
        if p.is_file():
            return p
    raise FileNotFoundError(f"Not found any of {names} in {folder}")


def load_production_and_downtime():
    """Load good / low bad / high bad + downtime CSVs."""
    dfs = []
    for label, names in [
        ("good", ["good.csv"]),
        ("low_bad", ["low bad.csv", "low_bad.csv"]),
        ("high_bad", ["high bad.csv", "high_bad.csv"]),
    ]:
        path = _find_file(DATA_MAIN, names)
        df = pd.read_csv(path)
        df["quality"] = label
        dfs.append(df)
    prod = pd.concat(dfs, ignore_index=True)

    downtime = None
    if DATA_DOWNTIME.is_dir():
        try:
            dt_path = _find_file(DATA_DOWNTIME, ["Yeast Prep DT 04_05_20 - 01_07_20.csv"])
            downtime = pd.read_csv(dt_path)
            date_col = [c for c in downtime.columns if "date" in c.lower()]
            if date_col:
                downtime["date"] = pd.to_datetime(downtime[date_col[0]], dayfirst=True).dt.normalize()
        except FileNotFoundError:
            pass

    return prod, downtime


def add_rolling_features(prod: pd.DataFrame, sp_cols: list, window: int = 3) -> pd.DataFrame:
    """Add rolling mean (window=3) per Part group on SP + key sensor columns."""
    prod = prod.copy()
    sensor_roll_cols = [
        "FFTE Production solids PV", "FFTE Feed solids PV",
        "TFE Production solids PV", "TFE Steam pressure PV",
        "TFE Vacuum pressure PV", "TFE Motor speed",
    ]
    roll_cols = [c for c in sp_cols + sensor_roll_cols if c in prod.columns]
    prod = prod.sort_values(["Part", "Set Time"])
    for col in roll_cols:
        roll_name = f"{col}_roll{window}"
        prod[roll_name] = (
            prod.groupby("Part")[col]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )
    return prod


def preprocessing(
    prod: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    use_rolling: bool = True,
):
    """Time-aware split 70/15/15, feature engineering, outlier clipping."""
    key_cols = ["VYP batch", "Set Time"]
    prod = prod.drop_duplicates(subset=key_cols, keep="first").copy()
    prod["Set Time"] = pd.to_datetime(prod["Set Time"], dayfirst=True)
    prod["date"] = prod["Set Time"].dt.normalize()
    prod["hour"] = prod["Set Time"].dt.hour
    prod["dow"] = prod["Set Time"].dt.dayofweek
    prod["month"] = prod["Set Time"].dt.month

    meta = ["VYP batch", "Part", "Set Time", "date", "quality"]
    sp_cols = [c for c in prod.columns if c.endswith(" SP")]
    other_num = [
        c for c in prod.columns
        if c not in meta and not c.endswith(" SP") and prod[c].dtype in ("float64", "int64")
    ]

    if use_rolling:
        prod = add_rolling_features(prod, sp_cols, window=3)
        roll_cols = [c for c in prod.columns if "_roll" in c]
    else:
        roll_cols = []

    feature_cols = sp_cols + other_num + roll_cols
    prod["Part_enc"] = LabelEncoder().fit_transform(prod["Part"].astype(str))
    use_cols = [c for c in feature_cols if c in prod.columns] + ["Part_enc"]

    X = prod[use_cols].astype(float)
    medians = X.median().to_dict()
    X = X.fillna(medians)

    le_q = LabelEncoder()
    y = le_q.fit_transform(prod["quality"])

    prod_sorted = prod.sort_values("Set Time")
    idx = prod_sorted.index.to_list()
    n = len(idx)
    t1, t2 = int(n * train_ratio), int(n * (train_ratio + val_ratio))
    tr_idx, val_idx, te_idx = idx[:t1], idx[t1:t2], idx[t2:]

    X_tr, X_val, X_te = X.loc[tr_idx].copy(), X.loc[val_idx].copy(), X.loc[te_idx].copy()
    y_tr = y[prod.index.get_indexer(tr_idx)]
    y_val = y[prod.index.get_indexer(val_idx)]
    y_te = y[prod.index.get_indexer(te_idx)]

    for c in X_tr.columns:
        q1, q3 = X_tr[c].quantile(0.25), X_tr[c].quantile(0.75)
        iqr = q3 - q1
        lo, hi = (q1 - 1.5 * iqr, q3 + 1.5 * iqr) if iqr > 0 else (X_tr[c].min(), X_tr[c].max())
        X_tr[c] = X_tr[c].clip(lo, hi)
        X_val[c] = X_val[c].clip(lo, hi)
        X_te[c] = X_te[c].clip(lo, hi)

    return X_tr, X_val, X_te, y_tr, y_val, y_te, prod, use_cols, le_q, medians, sp_cols


def train_quality_model(X_tr, y_tr, X_val, y_val, le_q):
    """Multiclass XGBoost with SMOTE + calibration."""
    # SMOTE oversampling
    if _HAS_SMOTE:
        class_counts = np.bincount(y_tr)
        min_count = class_counts.min()
        k_neighbors = min(5, min_count - 1) if min_count > 1 else 1
        try:
            smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=k_neighbors)
            X_tr_res, y_tr_res = smote.fit_resample(X_tr, y_tr)
            X_tr_res = pd.DataFrame(X_tr_res, columns=X_tr.columns)
        except Exception:
            X_tr_res, y_tr_res = X_tr, y_tr
    else:
        # Fallback: manual 2× oversample of low_bad
        X_tr_res, y_tr_res = X_tr.copy(), y_tr.copy()
        if "low_bad" in le_q.classes_:
            low_idx = list(le_q.classes_).index("low_bad")
            low_mask = y_tr == low_idx
            if low_mask.any():
                X_tr_res = pd.concat([X_tr_res, X_tr.iloc[np.where(low_mask)[0]]], axis=0).reset_index(drop=True)
                y_tr_res = np.concatenate([y_tr_res, y_tr[low_mask]])

    classes = np.unique(y_tr_res)
    class_weights = compute_class_weight("balanced", classes=classes, y=y_tr_res)
    sample_weights = np.array([class_weights[c] for c in y_tr_res])
    if "low_bad" in le_q.classes_:
        low_idx = list(le_q.classes_).index("low_bad")
        sample_weights[y_tr_res == low_idx] *= 2.0

    model = xgb.XGBClassifier(
        n_estimators=600,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=1.0,
        gamma=0.0,
        reg_lambda=1.0,
        reg_alpha=0.0,
        random_state=RANDOM_STATE,
        eval_metric="mlogloss",
        n_jobs=-1,
    )
    model.fit(X_tr_res, y_tr_res, sample_weight=sample_weights)

    if _HAS_CALIBRATION and len(X_val) >= 10 and len(np.unique(y_val)) >= 2:
        from sklearn.calibration import CalibratedClassifierCV
        cal = CalibratedClassifierCV(model, cv="prefit", method="isotonic")
        cal.fit(X_val, y_val)
        return cal
    return model


def train_per_part_models(prod, X_tr, y_tr, X_val, y_val, use_cols, le_q):
    """Train one calibrated XGBoost per yeast type."""
    part_models = {}
    for part in sorted(prod["Part"].unique()):
        part_tr_mask = (prod.loc[X_tr.index, "Part"] == part).values
        part_val_mask = (prod.loc[X_val.index, "Part"] == part).values
        X_p_tr = X_tr.iloc[np.where(part_tr_mask)[0]]
        y_p_tr = y_tr[part_tr_mask]
        X_p_val = X_val.iloc[np.where(part_val_mask)[0]]
        y_p_val = y_val[part_val_mask]

        if len(y_p_tr) < 20 or len(np.unique(y_p_tr)) < 2:
            continue

        if _HAS_SMOTE:
            class_counts = np.bincount(y_p_tr)
            min_count = class_counts[class_counts > 0].min()
            k_neighbors = min(5, min_count - 1) if min_count > 1 else 1
            try:
                smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=k_neighbors)
                X_p_res, y_p_res = smote.fit_resample(X_p_tr, y_p_tr)
                X_p_res = pd.DataFrame(X_p_res, columns=X_p_tr.columns)
            except Exception:
                X_p_res, y_p_res = X_p_tr, y_p_tr
        else:
            X_p_res, y_p_res = X_p_tr, y_p_tr

        classes = np.unique(y_p_res)
        class_weights = compute_class_weight("balanced", classes=classes, y=y_p_res)
        sample_weights = np.array([class_weights[c] for c in y_p_res])

        model = xgb.XGBClassifier(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, eval_metric="mlogloss", n_jobs=-1,
        )
        model.fit(X_p_res, y_p_res, sample_weight=sample_weights)

        if _HAS_CALIBRATION and len(y_p_val) >= 10 and len(np.unique(y_p_val)) >= 2:
            from sklearn.calibration import CalibratedClassifierCV
            cal = CalibratedClassifierCV(model, cv="prefit", method="isotonic")
            cal.fit(X_p_val, y_p_val)
            part_models[part] = cal
        else:
            part_models[part] = model

    return part_models


def train_downtime_model(prod, downtime, use_cols):
    """Binary downtime model."""
    if downtime is None or "date" not in downtime.columns:
        return None

    dt_dates = set(downtime["date"].dropna().dt.normalize().unique())
    prod = prod.copy()
    prod["downtime"] = prod["date"].isin(dt_dates).astype(int)

    mask = prod["downtime"].isin([0, 1])
    Xd = prod.loc[mask, use_cols].astype(float)
    Xd = Xd.fillna(Xd.median())
    yd = prod.loc[mask, "downtime"].values

    if len(np.unique(yd)) < 2:
        return None

    strat = prod.loc[mask, "Part"].values
    Xdt, Xdv, ydt, ydv = train_test_split(
        Xd, yd, test_size=0.25, stratify=strat, random_state=RANDOM_STATE
    )
    scale_pos = (ydt == 0).sum() / max((ydt == 1).sum(), 1)
    m2 = xgb.XGBClassifier(
        n_estimators=200, max_depth=6,
        random_state=RANDOM_STATE, eval_metric="logloss",
        n_jobs=-1, scale_pos_weight=scale_pos,
    )
    m2.fit(Xdt, ydt)
    return m2


def recommend_sp_joint(
    current_row: dict,
    quality_model,
    downtime_model,
    use_cols: list,
    sp_cols: list,
    le_q: LabelEncoder,
    medians: dict,
    prod_train: pd.DataFrame,
    n_grid: int = 3,
    lambda_downtime: float = 0.3,
):
    """
    Joint grid search over ALL SPs simultaneously.
    n_grid=3 per SP → 3^7 = 2187 candidates, batch-predicted.
    """
    good_idx = list(le_q.classes_).index("good") if "good" in le_q.classes_ else 0
    bounds = {
        c: (prod_train[c].quantile(0.25), prod_train[c].quantile(0.75))
        for c in sp_cols if c in prod_train.columns
    }
    base = {c: current_row.get(c, medians.get(c, 0.0)) for c in use_cols}
    sp_list = [c for c in sp_cols if c in bounds]

    sp_grids = [np.linspace(bounds[c][0], bounds[c][1], n_grid) for c in sp_list]
    candidates = []
    for combo in itertools.product(*sp_grids):
        cand = base.copy()
        for col, val in zip(sp_list, combo):
            cand[col] = float(val)
        candidates.append(cand)

    X_cands = pd.DataFrame(candidates)[use_cols]
    pgood_arr = quality_model.predict_proba(X_cands)[:, good_idx]
    pdt_arr = (
        downtime_model.predict_proba(X_cands)[:, 1]
        if downtime_model is not None
        else np.zeros(len(candidates))
    )
    scores = pgood_arr - lambda_downtime * pdt_arr
    best_idx = int(np.argmax(scores))
    best_cand = candidates[best_idx]
    rec_sp = {c: float(best_cand[c]) for c in sp_cols if c in best_cand}
    return rec_sp, float(pgood_arr[best_idx]), float(pdt_arr[best_idx])


# --------- Load or train models once at startup ---------

try:
    _PROD, _DOWNTIME = load_production_and_downtime()
    (
        _X_TR, _X_VAL, _X_TE, _Y_TR, _Y_VAL, _Y_TE,
        _PROD_FULL, _USE_COLS, _LE_Q, _MEDIANS, _SP_COLS,
    ) = preprocessing(_PROD, use_rolling=True)

    # Try loading from joblib first
    _M1 = None
    _M1_PER_PART = {}
    _M2 = None

    if joblib:
        if TASK1_MODEL_PATH.exists():
            try:
                _M1 = joblib.load(TASK1_MODEL_PATH)
                sys.stderr.write("Loaded global quality model from joblib\n")
            except Exception as e:
                sys.stderr.write(f"Failed to load task1 model: {e}\n")

        if TASK1_PER_PART_PATH.exists():
            try:
                _M1_PER_PART = joblib.load(TASK1_PER_PART_PATH)
                sys.stderr.write(f"Loaded per-Part models: {list(_M1_PER_PART.keys())}\n")
            except Exception as e:
                sys.stderr.write(f"Failed to load per-Part models: {e}\n")

        if TASK2_MODEL_PATH.exists():
            try:
                _M2 = joblib.load(TASK2_MODEL_PATH)
                sys.stderr.write("Loaded downtime model from joblib\n")
            except Exception as e:
                sys.stderr.write(f"Failed to load task2 model: {e}\n")

        if ARTIFACTS_PATH.exists():
            try:
                artifacts = joblib.load(ARTIFACTS_PATH)
                _LE_Q = artifacts["le_q"]
                _USE_COLS = artifacts["use_cols"]
                _SP_COLS = artifacts["sp_cols"]
                _MEDIANS = artifacts["medians"]
                _PART_TARGET_ENC = artifacts.get("part_target_enc", {})
                sys.stderr.write("Loaded artifacts from joblib\n")
            except Exception as e:
                sys.stderr.write(f"Failed to load artifacts: {e}\n")

    # Train missing models
    if _M1 is None:
        sys.stderr.write("Training global quality model...\n")
        _M1 = train_quality_model(_X_TR, _Y_TR, _X_VAL, _Y_VAL, _LE_Q)

    if not _M1_PER_PART:
        sys.stderr.write("Training per-Part models...\n")
        _M1_PER_PART = train_per_part_models(
            _PROD_FULL, _X_TR, _Y_TR, _X_VAL, _Y_VAL, _USE_COLS, _LE_Q
        )

    if _M2 is None:
        sys.stderr.write("Training downtime model...\n")
        _M2 = train_downtime_model(_PROD_FULL, _DOWNTIME, _USE_COLS)

    # Save if joblib available
    if joblib:
        try:
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(_M1, TASK1_MODEL_PATH)
            joblib.dump(_M1_PER_PART, TASK1_PER_PART_PATH)
            if _M2 is not None:
                joblib.dump(_M2, TASK2_MODEL_PATH)
            joblib.dump({
                "le_q": _LE_Q, "use_cols": _USE_COLS,
                "sp_cols": _SP_COLS, "medians": _MEDIANS,
            }, ARTIFACTS_PATH)
            sys.stderr.write("Saved models to joblib files\n")
        except Exception as e:
            sys.stderr.write(f"Failed to save models: {e}\n")

except Exception as e:
    print(json.dumps({"error": f"Model init failed: {e}"}))
    sys.exit(1)


def _get_model_for_part(part: str):
    """Return the per-Part model if available, else global model."""
    if part and part in _M1_PER_PART:
        return _M1_PER_PART[part]
    return _M1


def main() -> None:
    raw = sys.stdin.read()
    try:
        body = json.loads(raw or "{}")
    except json.JSONDecodeError:
        body = {}

    # --- Build current row from all 7 SP inputs ---
    current = {c: float(v) for c, v in _MEDIANS.items()}

    # Map all 7 UI SP keys to canonical column names
    for ui_key, col_name in UI_TO_SP.items():
        if ui_key in body and body[ui_key] is not None:
            if col_name in current:
                current[col_name] = float(body[ui_key])

    # Merge sensor PV values if provided (overriding medians)
    sensors = body.get("sensors", {})
    if isinstance(sensors, dict):
        for k, v in sensors.items():
            # Only use sensors that are actually features in the model
            if k in current and v is not None:
                try:
                    current[k] = float(v)
                except (ValueError, TypeError):
                    pass

    # Set Part_enc from the 'part' field
    part_str = str(body.get("part", "Yeast - BRD"))
    if "Part_enc" in current and "Part" in _PROD_FULL.columns:
        enc = LabelEncoder().fit(_PROD_FULL["Part"].astype(str))
        try:
            current["Part_enc"] = float(enc.transform([part_str])[0])
        except ValueError:
            current["Part_enc"] = float(_PROD_FULL["Part_enc"].median())

    # Set Part_target_enc check
    if "Part_target_enc" in current:
        # Default to 1.0 (neutral) if not found in map
        current["Part_target_enc"] = float(_PART_TARGET_ENC.get(part_str, 1.0))

    # Select model: per-Part if available, else global
    quality_model = _get_model_for_part(part_str)

    # Training data bounds for prescriptive (use all training rows)
    prod_train = _PROD_FULL.loc[_X_TR.index]

    # --- Joint SP optimization ---
    rec_sp, p_good_rec, p_dt_rec = recommend_sp_joint(
        current_row=current,
        quality_model=quality_model,
        downtime_model=_M2,
        use_cols=_USE_COLS,
        sp_cols=_SP_COLS,
        le_q=_LE_Q,
        medians=_MEDIANS,
        prod_train=prod_train,
        n_grid=3,
        lambda_downtime=0.3,
    )

    # --- Current input prediction ---
    X_curr = pd.DataFrame([current])[_USE_COLS]
    pred_proba = quality_model.predict_proba(X_curr)[0]
    pred_idx = int(np.argmax(pred_proba))
    pred_label = str(_LE_Q.inverse_transform([pred_idx])[0]).upper()

    good_class_idx = list(_LE_Q.classes_).index("good") if "good" in _LE_Q.classes_ else 0
    current_p_good = float(pred_proba[good_class_idx])

    if _M2 is not None:
        current_p_dt = float(_M2.predict_proba(X_curr)[0][1])
    else:
        high_bad_idx = list(_LE_Q.classes_).index("high_bad") if "high_bad" in _LE_Q.classes_ else -1
        low_bad_idx = list(_LE_Q.classes_).index("low_bad") if "low_bad" in _LE_Q.classes_ else -1
        p_high = float(pred_proba[high_bad_idx]) if high_bad_idx >= 0 else 0.0
        p_low = float(pred_proba[low_bad_idx]) if low_bad_idx >= 0 else 0.0
        current_p_dt = min(1.0, p_high * 0.8 + p_low * 0.3)

    # --- Map recommended SPs back to UI keys ---
    ui_rec = {ui_key: float(rec_sp.get(col_name, current.get(col_name, 0.0)))
              for ui_key, col_name in UI_TO_SP.items()}

    out = {
        "recommendedSP": ui_rec,
        "pGood": float(round(current_p_good, 4)),
        "pDowntime": float(round(current_p_dt, 4)),
        "prediction": pred_label,
        "downtimeRisk": float(round(current_p_dt * 100.0, 2)),
        "recommendedPGood": float(round(p_good_rec, 4)),
        "recommendedPDowntime": float(round(p_dt_rec, 4)),
    }
    sys.stdout.write(json.dumps(out))


if __name__ == "__main__":
    main()
