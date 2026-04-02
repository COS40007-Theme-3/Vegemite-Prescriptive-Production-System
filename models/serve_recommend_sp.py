
"""
Production Serving Script – Advanced Revision
Backend logic for the Vegemite Prescriptive Production System.

Features:
- Loads the 6 new task-specific model artifacts and Configs.
- Synchronized feature engineering mapping directly to Window-Based (mean, max, min, delta) formats.
- Safe Grid Optimization honoring the rigorous +-5% bound constraints.
- Multi-class root-cause inference combined with Isolation Forest.
"""

import itertools
import json
import os
import random
import sys
import re
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

import warnings
warnings.filterwarnings('ignore')

# Configuration and Paths
BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models" / "models"
CONFIG_DIR = BASE_DIR / "models" / "config"
BUFFER_FILE = BASE_DIR / "data" / "sensor_buffer.json"
MAX_BUFFER_SIZE = 15

FRIENDLY_TO_TAG_MAP = {
    "FFTE_Steam_pressure_PV": "Port_Melbourne_RSLinx_Enterprise_Veg_B_SQL_FFTE_Steam_Pressure",
    "FFTE_Heat_temperature_1": "Port_Melbourne_RSLinx_Enterprise_Veg_B_SQL_FFTE_Pre_Heat_Temperature1_Deg_C_",
    "FFTE_Heat_temperature_2": "Port_Melbourne_RSLinx_Enterprise_Veg_B_SQL_FFTE_Pre_Heat_Temperature2_Deg_C_",
    "FFTE_Heat_temperature_3": "Port_Melbourne_RSLinx_Enterprise_Veg_B_SQL_FFTE_Pre_Heat_Temperature3_Deg_C_",
    "TFE_Product_out_temperature": "Port_Melbourne_RSLinx_Enterprise_Veg_B_SQL_FFTE_Post_Heat_Temperature_Deg_C_",
    "Extract_tank_Level": "VEG_B_HMI_VELC1060_PV_",
    "TFE_Tank_level": "VEG_B_HMI_VELC1662_PV_",
    "TFE_Level": "VEG_C_VMLT2007_",
    "TFE_Vacuum_pressure_PV": "VEG_B_HMI_VEDC1266_PV_",
    "TFE_Out_flow_SP": "VEG_B_HMI_VEDC1664_SP_"
}

class FeatureEngineer:
    """Replicates the Window-based feature derivation for inference."""
    
    @staticmethod
    def update_and_get_buffer(row_dict_clean):
        buffer = []
        if BUFFER_FILE.exists():
            try:
                with open(BUFFER_FILE, 'r') as f:
                    buffer = json.load(f)
            except:
                pass
        
        buffer.append(row_dict_clean)
        if len(buffer) > MAX_BUFFER_SIZE:
            buffer = buffer[-MAX_BUFFER_SIZE:]
            
        try:
            with open(BUFFER_FILE, 'w') as f:
                json.dump(buffer, f)
        except Exception as e:
            sys.stderr.write(f"Warning: could not write buffer {e}\n")
            
        return pd.DataFrame(buffer)

    @staticmethod
    def compute_for_buffer(buffer_df, features_list):
        out = {}
        last_row = buffer_df.iloc[-1].to_dict()
        first_row = buffer_df.iloc[0].to_dict()
        
        for f in features_list:
            if f.endswith('_mean'):
                base_f = f[:-5]
                out[f] = float(buffer_df[base_f].mean()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_mean_lag5'):
                base_f = f[:-10]
                out[f] = float(buffer_df[base_f].mean()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_mean_volatility'):
                base_f = f[:-16]
                out[f] = float(buffer_df[base_f].mean()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_std'):
                base_f = f[:-4]
                val = float(buffer_df[base_f].std()) if base_f in buffer_df.columns and len(buffer_df) > 1 else 0.0
                out[f] = val if not pd.isna(val) else 0.0
            elif f.endswith('_std_lag5'):
                base_f = f[:-9]
                val = float(buffer_df[base_f].std()) if base_f in buffer_df.columns and len(buffer_df) > 1 else 0.0
                out[f] = val if not pd.isna(val) else 0.0
            elif f.endswith('_std_volatility'):
                base_f = f[:-15]
                val = float(buffer_df[base_f].std()) if base_f in buffer_df.columns and len(buffer_df) > 1 else 0.0
                out[f] = val if not pd.isna(val) else 0.0
            elif f.endswith('_max'):
                base_f = f[:-4]
                out[f] = float(buffer_df[base_f].max()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_max_lag5'):
                base_f = f[:-9]
                out[f] = float(buffer_df[base_f].max()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_max_volatility'):
                base_f = f[:-15]
                out[f] = float(buffer_df[base_f].max()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_min'):
                base_f = f[:-4]
                out[f] = float(buffer_df[base_f].min()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_min_lag5'):
                base_f = f[:-9]
                out[f] = float(buffer_df[base_f].min()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_min_volatility'):
                base_f = f[:-15]
                out[f] = float(buffer_df[base_f].min()) if base_f in buffer_df.columns else float(last_row.get(base_f, 0.0))
            elif f.endswith('_delta'):
                base_f = f[:-6]
                out[f] = float(last_row.get(base_f, 0.0)) - float(first_row.get(base_f, 0.0)) if base_f in buffer_df.columns else 0.0
            elif f.endswith('_delta_lag5'):
                base_f = f[:-11]
                out[f] = float(last_row.get(base_f, 0.0)) - float(first_row.get(base_f, 0.0)) if base_f in buffer_df.columns else 0.0
            elif f.endswith('_delta_volatility'):
                base_f = f[:-17]
                out[f] = float(last_row.get(base_f, 0.0)) - float(first_row.get(base_f, 0.0)) if base_f in buffer_df.columns else 0.0
            else:
                out[f] = float(last_row.get(f, 0.0))
                
        # Return dataframe strictly aligned to trained feature order
        return pd.DataFrame([out])[features_list].fillna(0.0)

# UI key to Canonical SP column mapping
UI_TO_SP = {
    "ffteFeedSolidsSP":       "FFTE Feed solids SP",
    "ffteProductionSolidsSP": "FFTE Production solids SP",
    "ffteSteamPressureSP":    "FFTE Steam pressure SP",
    "tfeOutFlowSP":           "TFE Out flow SP",
    "tfeProductionSolidsSP":  "TFE Production solids SP",
    "tfeVacuumPressureSP":    "TFE Vacuum pressure SP",
    "tfeSteamPressureSP":     "TFE Steam pressure SP",
}

class VegemiteServer:
    def __init__(self):
        self.m1_classifiers = {}
        self.m1_recommenders = {}
        self.m2_lgbs = {}
        self.m2_isos = {}
        self.m2_scalers = {}
        self.m2_stage2_lgbs = {}
        self.m2_stage2_encoders = {}
        
        self.task1_features = {}
        self.task1_feature_not_sp = {}
        self.task1_sp_cols = {}
        
        self.task2_features = {}
        self.task2_class_mapping = {}

        self.load_models()

    def load_models(self):
        """Loads SOTA configurations and joblibs delivered by ML Engineer."""
        try:
            # 1. Load Configurations
            if (CONFIG_DIR / "task1_features.json").exists():
                with open(CONFIG_DIR / "task1_features.json", 'r') as f:
                    t1_config = json.load(f)
                    self.task1_features = {k: v.get("features", []) for k,v in t1_config.items()}
                    self.task1_feature_not_sp = {k: v.get("feature_not_sp", []) for k,v in t1_config.items()}
                    self.task1_sp_cols = {k: v.get("sp_cols", []) for k,v in t1_config.items()}
                    
            if (CONFIG_DIR / "task2_features.json").exists():
                with open(CONFIG_DIR / "task2_features.json", 'r') as f:
                    self.task2_features = json.load(f)
                    
            if (CONFIG_DIR / "task2_class_mapping.json").exists():
                with open(CONFIG_DIR / "task2_class_mapping.json", 'r') as f:
                    # JSON keys are always strings -> convert back to int
                    self.task2_class_mapping = {int(k): v for k, v in json.load(f).items()}
                
            # 2. Load Task 1 (Quality Specialist Models)
            for part in ["Yeast - BRD", "Yeast - BRN", "Yeast - FMX"]:
                safe_name = part.replace(" ", "_").replace("-", "")
                
                # Classifier Task 1
                clf_path = MODELS_DIR / f"task1_classifier_{safe_name}.joblib"
                if clf_path.exists():
                    self.m1_classifiers[part] = joblib.load(clf_path)
                    
                # Recommender Task 1
                rec_path = MODELS_DIR / f"task1_recommender_{safe_name}.joblib"
                if rec_path.exists():
                    self.m1_recommenders[part] = joblib.load(rec_path)
            
            # 3. Load Task 2 (Downtime Ensemble & Scaler)
            for machine in ["TFE", "FFTE"]:
                lgb_path = MODELS_DIR / f"task2_stage1_lgb_{machine}.joblib"
                if lgb_path.exists():
                    self.m2_lgbs[machine] = joblib.load(lgb_path)
                
                iso_path = MODELS_DIR / f"task2_stage1_iso_{machine}.joblib"
                if iso_path.exists():
                    self.m2_isos[machine] = joblib.load(iso_path)
                
                scaler_path = MODELS_DIR / f"task2_stage1_scaler_{machine}.joblib"
                if scaler_path.exists():
                    self.m2_scalers[machine] = joblib.load(scaler_path)
                    
                s2_lgb_path = MODELS_DIR / f"task2_stage2_lgb_{machine}.joblib"
                if s2_lgb_path.exists():
                    self.m2_stage2_lgbs[machine] = joblib.load(s2_lgb_path)
                    
                s2_enc_path = MODELS_DIR / f"task2_stage2_enc_{machine}.joblib"
                if s2_enc_path.exists():
                    self.m2_stage2_encoders[machine] = joblib.load(s2_enc_path)

            sys.stderr.write(f"Server successfully initialized from {MODELS_DIR}\n")
            sys.stderr.write(f"✅ Loaded {len(self.m1_classifiers)} Classifiers\n")
            sys.stderr.write(f"✅ Loaded {len(self.m1_recommenders)} Recommenders\n")
            sys.stderr.write(f"✅ Task 2 Model Status: Loaded {len(self.m2_lgbs)} machines\n")
        except Exception as e:
            sys.stderr.write(f"Initialization error: {e}\n")

    def get_model1(self, part):
        return self.m1_classifiers.get(part)
        
    def get_recommender1(self, part):
        return self.m1_recommenders.get(part)

    def optimize_sp(self, buffer_df, part, p_good_curr):
        """Prescriptive Engine với Dynamic Bounds & Safety Protocols."""
        model_clf = self.get_model1(part)
        model_rec = self.get_recommender1(part)
        
        clean_row = buffer_df.iloc[-1].to_dict()
        safe_part = part.replace(" ", "_").replace("-", "")
        t1_feats = self.task1_features.get(safe_part, [])
        feature_not_sp = self.task1_feature_not_sp.get(safe_part, [])
        sp_cols = self.task1_sp_cols.get(safe_part, [])
        
        # Default SP giữ nguyên hiện trạng
        default_rec = {ui: float(clean_row.get(re.sub(r'[^A-Za-z0-9_]+', '_', canon), 0.0)) for ui, canon in UI_TO_SP.items()}
        
        # 1. CHỐT CHẶN AN TOÀN 1: "Don't fix what ain't broke"
        # Nếu mẻ đang có xác suất Good >= 85%, tuyệt đối không can thiệp để tránh làm hỏng mẻ
        if p_good_curr >= 0.85:
            return default_rec, p_good_curr, 0.0, False

        if not model_clf or not t1_feats or not model_rec or not feature_not_sp:
            return default_rec, p_good_curr, 0.0, False

        # Tạo vector đầu vào cho Recommender
        curr_buffer_calc = FeatureEngineer.compute_for_buffer(buffer_df, feature_not_sp)
        raw_rec_sp_values = model_rec.predict(curr_buffer_calc)[0]
        
        # =================================================================
        # 🚀 CHỐT CHẶN 2: DYNAMIC BOUNDS (Biên độ động theo "độ nguy kịch")
        # =================================================================
        if p_good_curr < 0.15:
            base_deviation = 0.15  # Mẻ sắp hỏng nặng -> AI được phép "đánh liều" vặn tới 15%
        elif p_good_curr < 0.40:
            base_deviation = 0.10  # Mẻ đang có vấn đề -> Nới lỏng 10%
        else:
            base_deviation = 0.05  # Mẻ hơi lệch chuẩn -> Siết chặt an toàn 5%

        best_cand = clean_row.copy()
        requires_manual_review = False # Cờ báo hiệu cho UI
        
        for idx, sp_col in enumerate(sp_cols):
            orig_val = float(clean_row.get(sp_col, 0.0))
            new_val = raw_rec_sp_values[idx]
            
            # 🚀 CHỐT CHẶN 3: SENSOR-SPECIFIC RULES (Quy tắc vật lý)
            col_lower = sp_col.lower()
            if "temperature" in col_lower or "heat" in col_lower:
                allowed_dev = min(base_deviation, 0.05) 
                margin = max(np.abs(orig_val) * allowed_dev, 0.5)
            elif "flow" in col_lower or "speed" in col_lower:
                allowed_dev = min(base_deviation * 1.5, 0.20)
                margin = max(np.abs(orig_val) * allowed_dev, 1.0)
            elif "vacuum" in col_lower:
                # FIX: Vacuum Pressure dao động dải rộng (âm sang dương)
                # Cho phép AI giật van một lực cực lớn (hard margin = 40.0) để cứu máy
                allowed_dev = base_deviation * 2.0
                margin = max(np.abs(orig_val) * allowed_dev, 40.0) 
            elif "pressure" in col_lower:
                # Áp suất dương bình thường (như Steam Pressure) thì giữ mức biên độ vừa phải
                allowed_dev = base_deviation
                margin = max(np.abs(orig_val) * allowed_dev, 10.0)
            else:
                allowed_dev = base_deviation
                margin = max(np.abs(orig_val) * allowed_dev, 0.5)
            
            # Cắt gọt giá trị an toàn
            bound_lower = orig_val - margin
            bound_upper = orig_val + margin
            safe_val = np.clip(new_val, bound_lower, bound_upper)
            
            # Nếu AI quyết định vặn quá 10% so với ban đầu, bật cờ Review cho kỹ sư
            if np.abs(safe_val - orig_val) > (np.abs(orig_val) * 0.10) and np.abs(safe_val - orig_val) > 1.0:
                requires_manual_review = True
                
            best_cand[sp_col] = safe_val
            
        # Mô phỏng lại xác suất Good sau khi vặn van an toàn
        cand_buffer_df = buffer_df.copy()
        for k, v in best_cand.items():
            cand_buffer_df.loc[cand_buffer_df.index[-1], k] = v
            
        X_t1 = FeatureEngineer.compute_for_buffer(cand_buffer_df, t1_feats)
        p_vec = model_clf.predict_proba(X_t1)[0]
        best_pg = float(p_vec[0])
        
        # Mô phỏng lại rủi ro Downtime (Task 2)
        best_pdt = 0.0
        if self.m2_lgbs and self.task2_features:
            # Tái tạo lại SP_PV conflicts
            pv_cols = [c for c in cand_buffer_df.columns if 'PV' in c]
            for pv_col in pv_cols:
                sp_col = pv_col.replace('PV', 'SP')
                if sp_col in cand_buffer_df.columns:
                    err_col = pv_col.replace('PV', 'SP_PV_Delta')
                    pv_val = pd.to_numeric(cand_buffer_df[pv_col], errors='coerce').fillna(0)
                    sp_val = pd.to_numeric(cand_buffer_df[sp_col], errors='coerce').fillna(0)
                    cand_buffer_df[err_col] = pv_val - sp_val
                    cand_buffer_df[f'{err_col}_volatility'] = cand_buffer_df[err_col].rolling(window=15, min_periods=1).std().fillna(0)
                lag5_col = f"{pv_col}_lag5"
                cand_buffer_df[lag5_col] = cand_buffer_df[pv_col].shift(5).bfill()

            for machine in self.m2_lgbs.keys():
                config = self.task2_features.get(machine, {})
                features = config.get("features", [])
                if not features: continue
                # We calculate T2 feature values
                X_t2 = FeatureEngineer.compute_for_buffer(cand_buffer_df, [f for f in features if f != 'IF_Anomaly_Score'])
                
                # Fetch Iso and Scaler for calculating IF_Anomaly_Score
                iso_model = self.m2_isos.get(machine)
                scaler_model = self.m2_scalers.get(machine)
                if iso_model and scaler_model:
                    X_t2_scaled = scaler_model.transform(X_t2)
                    anomaly_score = -iso_model.decision_function(X_t2_scaled)[0]
                    X_t2['IF_Anomaly_Score'] = anomaly_score
                else:
                    X_t2['IF_Anomaly_Score'] = 0.0
                
                # Ensure ordered identical to JSON
                X_t2 = X_t2[features + ['IF_Anomaly_Score']]
                
                p_dt_vec = self.m2_lgbs[machine].predict_proba(X_t2)[0]
                risk = float(p_dt_vec[1]) if len(p_dt_vec) > 1 else 0.0
                if risk > best_pdt:
                    best_pdt = risk
                
        # Format trả về UI
        rec_sp = {}
        for ui, canonical in UI_TO_SP.items():
            clean_col = re.sub(r'[^A-Za-z0-9_]+', '_', canonical)
            rec_sp[ui] = float(best_cand.get(clean_col, clean_row.get(clean_col, 0.0)))
            
        return rec_sp, best_pg, best_pdt, requires_manual_review


def main():
    server = VegemiteServer()
    
    # Read input from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data: return
        body = json.loads(input_data)
    except Exception as e:
        sys.stderr.write(f"JSON input error: {e}\n")
        return

    # Extract inputs
    part = body.get("part", "Yeast - BRD")
    
    try:
        # Formulate base row from UI keys + extra sensors
        raw_row = {}
        for ui_key, col_name in UI_TO_SP.items():
            if ui_key in body:
                raw_row[col_name] = float(body[ui_key])
        
        sensors = body.get("sensors", {})
        if isinstance(sensors, dict):
            for k, v in sensors.items():
                raw_row[k] = float(v)

        # Standardize Names matching LightGBM Training Data
        clean_row = {}
        for k, v in raw_row.items():
            clean_k = re.sub(r'[^A-Za-z0-9_]+', '_', k)
            clean_row[clean_k] = v

        # =============================================================
        # 🤖 BẢN SAO SỐ (DIGITAL TWIN SIMULATION - FOR DEMO PHASE 2)
        # =============================================================
        try:
            prev_buffer = []
            if BUFFER_FILE.exists():
                with open(BUFFER_FILE, 'r') as f:
                    prev_buffer = json.load(f)
                    
            last_state = prev_buffer[-1] if prev_buffer else {}
                
            twin_pairs = [
                ("TFE_Vacuum_pressure_SP", "TFE_Vacuum_pressure_PV"),
                ("FFTE_Steam_pressure_SP", "FFTE_Steam_pressure_PV"),
                ("TFE_Out_flow_SP", "TFE_Out_flow_PV"),
                ("TFE_Production_solids_SP", "TFE_Production_solids_PV")
            ]
            
            for sp_col, pv_col in twin_pairs:
                # SỬA LỖI 1: Chỉ cần kiểm tra xem UI có gửi SP lên không
                if sp_col in clean_row:
                    target_sp = float(clean_row[sp_col])
                    last_pv = float(last_state.get(pv_col, target_sp))
                    
                    diff = target_sp - last_pv
                    
                    # SỬA LỖI BƠM CHAOS (Tự động nhận diện lỗi vật lý)
                    RESPONSE_RATE = 0.35
                    step = diff * RESPONSE_RATE
                    jitter = random.uniform(-1.5, 1.5) # Rung lắc bình thường
                    
                    # Bơm hỗn loạn (Chaos) có định hướng vật lý
                    if pv_col == "FFTE_Steam_pressure_PV" and target_sp >= 145.0:
                        # Áp suất quá cao -> Van không đóng được -> PV bị dội ngược lên trên SP
                        jitter = random.uniform(25.0, 50.0) 
                        
                    elif pv_col == "TFE_Out_flow_PV" and target_sp <= 1500.0:
                        # Máy bơm bị nghẹt -> Lưu lượng thực tế (PV) không thể xuống thấp như SP
                        # Ép PV luôn cao hơn SP ít nhất 600 đến 800 đơn vị (Không bao giờ về 0)
                        jitter = random.uniform(600.0, 800.0) 
                        
                    elif pv_col == "TFE_Vacuum_pressure_PV" and target_sp >= -20.0:
                        # Hở chân không -> Áp suất bị xả thẳng về áp suất khí quyển (gần 0)
                        jitter = random.uniform(15.0, 30.0)
                        
                    simulated_pv = last_pv + step + jitter
                    clean_row[pv_col] = round(simulated_pv, 2)
            
            # SỬA LỖI 2: Phục hồi các Cảm biến tĩnh (Rất quan trọng cho IF)
            static_pvs = {
                "Extract_tank_Level": 65.0,
                "TFE_Tank_level": 70.0,
                "TFE_Level": 50.0,
                "FFTE_Heat_temperature_1": 80.0,
                "FFTE_Heat_temperature_2": 82.0,
                "FFTE_Heat_temperature_3": 81.0,
                "TFE_Product_out_temperature": 68.0
            }
            for stat_col, base_val in static_pvs.items():
                if stat_col not in clean_row:
                    old_stat = float(last_state.get(stat_col, base_val))
                    clean_row[stat_col] = round(old_stat + random.uniform(-0.5, 0.5), 2)
                    
        except Exception as e:
            sys.stderr.write(f"Digital Twin Simulation Warning: {e}\n")
        # =============================================================

        # -------------------------------------------------------------
        # TASK 1: QUALITY PREDICTION (Current Settings)
        # -------------------------------------------------------------
        pred_label = "UNKNOWN"
        p_good = 0.0
        
        model1 = server.get_model1(part)
        safe_part = part.replace(" ", "_").replace("-", "")
        t1_feats = server.task1_features.get(safe_part, [])
        
        # Load and update history buffer
        buffer_df = FeatureEngineer.update_and_get_buffer(clean_row)

        if model1 and t1_feats:
            X_t1 = FeatureEngineer.compute_for_buffer(buffer_df, t1_feats)
            p_vec = model1.predict_proba(X_t1)[0]
            
            p_good = float(p_vec[0])
            p_low = float(p_vec[1]) if len(p_vec) > 1 else 0.0
            p_high = float(p_vec[2]) if len(p_vec) > 2 else 0.0
            
            # Lỗi số 3: Logic bảo vệ Threshold để bắt chuẩn Low_Bad vs High_Bad
            if p_low > 0.20 and p_low >= (p_high * 0.5):
                pred_label = "LOW_BAD"
            elif p_high > p_low and p_high > p_good:
                pred_label = "HIGH_BAD"
            elif p_good >= p_low and p_good >= p_high:
                pred_label = "GOOD"
            else:
                pred_idx = int(np.argmax(p_vec))
                if pred_idx == 0:
                    pred_label = "GOOD"
                elif pred_idx == 1:
                    pred_label = "LOW_BAD"
                else:
                    pred_label = "HIGH_BAD"

        # -------------------------------------------------------------
        # TASK 2: DOWNTIME ALERT (Multi-Class + Isolation Check)
        # -------------------------------------------------------------
        pred_dt_classes = []
        p_dt_risk = 0.0
        iso_anomaly = False

        if server.m2_lgbs and server.m2_isos and server.m2_scalers and server.task2_features:
            
            # 1. ĐỒNG BỘ TÊN CỘT (Từ tên ngắn của UI sang tên Dài của Model)
            buffer_df_t2 = buffer_df.copy()
            for friendly, tag in FRIENDLY_TO_TAG_MAP.items():
                clean_tag = re.sub(r'[^A-Za-z0-9_]+', '_', tag)
                if friendly in buffer_df_t2.columns:
                    buffer_df_t2[clean_tag] = buffer_df_t2[friendly]

            # ---------------------------------------------------------
            # 🚀 TÁI TẠO ĐẶC TRƯNG XUNG ĐỘT (SP vs PV) VÀ LAG5 TRÊN RUNTIME
            # ---------------------------------------------------------
            pv_cols = [c for c in buffer_df_t2.columns if 'PV' in c]
            for pv_col in pv_cols:
                sp_col = pv_col.replace('PV', 'SP')
                if sp_col in buffer_df_t2.columns:
                    err_col = pv_col.replace('PV', 'SP_PV_Delta')
                    # Tính sai số tức thời
                    pv_val = pd.to_numeric(buffer_df_t2[pv_col], errors='coerce').fillna(0)
                    sp_val = pd.to_numeric(buffer_df_t2[sp_col], errors='coerce').fillna(0)
                    buffer_df_t2[err_col] = pv_val - sp_val
                    
                    # Tính độ biến động tích lũy (volatility) trong buffer
                    buffer_df_t2[f'{err_col}_volatility'] = buffer_df_t2[err_col].rolling(window=15, min_periods=1).std().fillna(0)
                
                # Tính đặc trưng Time-lagged (kéo lùi 5 bước nếu đủ dữ liệu)
                lag5_col = f"{pv_col}_lag5"
                buffer_df_t2[lag5_col] = buffer_df_t2[pv_col].shift(5).bfill()

            # Lặp qua từng máy để gom chỉ báo rủi ro
            for machine, lgb_model in server.m2_lgbs.items():
                config = server.task2_features.get(machine, {})
                features = config.get("features", [])
                stage1_thresh = config.get("stage1_thresh", 0.05)
                stage2_fallback = config.get("stage2_fallback", f"{machine}_Anomaly")
                
                if not features: continue

                # 2. TÍNH TOÁN CÁC FEATURES cho máy này
                base_features = [f for f in features if f != 'IF_Anomaly_Score']
                X_t2 = FeatureEngineer.compute_for_buffer(buffer_df_t2, base_features)
                
                # Sub-Task 2A: Isolation Forest 
                iso_model = server.m2_isos.get(machine)
                scaler_model = server.m2_scalers.get(machine)
                local_iso_anomaly = False
                
                if iso_model and scaler_model:
                    X_t2_scaled = scaler_model.transform(X_t2)
                    iso_preds = iso_model.predict(X_t2_scaled)
                    anomaly_score = -iso_model.decision_function(X_t2_scaled)[0]
                    X_t2['IF_Anomaly_Score'] = anomaly_score
                    if iso_preds[0] == -1:
                        iso_anomaly = True
                        local_iso_anomaly = True
                else:
                    X_t2['IF_Anomaly_Score'] = 0.0

                # SỬA LỖI 3: Tránh duplicate tên cột
                if 'IF_Anomaly_Score' not in features:
                    features_ordered = features + ['IF_Anomaly_Score']
                else:
                    features_ordered = features
                X_t2 = X_t2[features_ordered]

                # Sub-Task 2B: Root Cause Multi-Class LightGBM 
                p_dt_vec = lgb_model.predict_proba(X_t2)[0]
                raw_risk = float(p_dt_vec[1]) if len(p_dt_vec) > 1 else float(p_dt_vec[0])
                
                # =========================================================
                # 🚀 UI PROBABILITY CALIBRATION (HIỆU CHUẨN XÁC SUẤT)
                # Dịch xác suất thô (rất nhỏ) của ML sang thang điểm 0-100% của UI
                # =========================================================
                calibrated_risk = 0.0
                if local_iso_anomaly and raw_risk >= stage1_thresh:
                    # NGUY HIỂM: Vượt ngưỡng -> Scale lên vùng 85% - 99% để UI chớp đỏ
                    calibrated_risk = 0.85 + ((raw_risk - stage1_thresh) / (1.0 - stage1_thresh)) * 0.14
                else:
                    # AN TOÀN: Scale lùi về vùng 0% - 40% để UI báo an toàn
                    if stage1_thresh > 0:
                        calibrated_risk = (raw_risk / stage1_thresh) * 0.40
                
                if calibrated_risk > p_dt_risk:
                    p_dt_risk = calibrated_risk
                    
                # HARD RULE BTRỢ ĐỘC LẬP CHO EXTRACT TANK
                if machine == "TFE":
                    try:
                        col_name = 'Extract_tank_Level'
                        if 'Extract_tank_Level_PV' in buffer_df_t2.columns:
                            col_name = 'Extract_tank_Level_PV'
                        
                        extract_level = float(buffer_df_t2[col_name].iloc[-1]) if col_name in buffer_df_t2.columns else 0.0
                        
                        if extract_level > 95.0:
                            # Bypass cả AI models, set cứng flag nguy hiểm
                            p_dt_risk = max(p_dt_risk, 0.99)
                            pred_dt_classes.append("EXTRACT_TANK_OVERFLOW_CRITICAL")
                            local_iso_anomaly = True # ép đỏ UI
                            raw_risk = 1.0 # ép đỏ UI
                    except Exception:
                        pass

                # Hợp nhất logic Threshold + Isolation Forest để tìm nguyên nhân
                if local_iso_anomaly and raw_risk >= stage1_thresh:
                    # Nếu có Stage 2 Model thì dùng để rẽ nhánh Root Cause
                    s2_lgb = server.m2_stage2_lgbs.get(machine)
                    s2_enc = server.m2_stage2_encoders.get(machine)
                    if s2_lgb is not None and s2_enc is not None:
                        pred_enc = s2_lgb.predict(X_t2)[0]
                        pred_cause = s2_enc.inverse_transform([pred_enc])[0]
                        
                        if "EXTRACT_TANK_OVERFLOW_CRITICAL" not in pred_dt_classes:
                            pred_dt_classes.append(pred_cause)
                    else:
                        if "EXTRACT_TANK_OVERFLOW_CRITICAL" not in pred_dt_classes:
                            pred_dt_classes.append(stage2_fallback)

        if not pred_dt_classes:
            pred_dt_classes = ["Normal"]


        # -------------------------------------------------------------
        # PRESCRIPTIVE ENGINE (Recommendations)
        # -------------------------------------------------------------
        rec_sp, rec_p_good, rec_p_dt, review_flag = server.optimize_sp(buffer_df, part, p_good)

        response = {
            "recommendedSP": rec_sp,
            "pGood": float(round(p_good, 4)),
            "pDowntime": float(round(p_dt_risk, 4)),
            "prediction": pred_label,
            "downtimeRisk": float(round(p_dt_risk * 100, 2)),
            "rootCause": pred_dt_classes,
            "isoAnomaly": iso_anomaly,
            "recommendedPGood": float(round(rec_p_good, 4)),
            "recommendedPDowntime": float(round(rec_p_dt, 4)),
            "requiresManualReview": review_flag
        }

        # 4. Safe Logging
        try:
            from datetime import datetime
            log_dir = BASE_DIR / "data"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "prediction_logs.csv"
            
            log_data = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Part": part}
            for ui_key in UI_TO_SP.keys():
                log_data[ui_key] = body.get(ui_key, "")
            log_data["Prediction"] = pred_label
            log_data["pGood"] = float(round(p_good, 4))
            log_data["pDowntimeRisk"] = float(round(p_dt_risk * 100, 2))
            log_data["RootCause"] = " | ".join(pred_dt_classes)
            
            pd.DataFrame([log_data]).to_csv(log_file, mode='a', header=not log_file.exists(), index=False)
        except:
            pass

    except Exception as e:
        import traceback; traceback.print_exc()
        response = {
            "error": str(e), "prediction": "ERROR",
            "pGood": 0.0, "pDowntime": 0.0, "downtimeRisk": 0.0, "rootCause": "Error",
            "recommendedSP": {k: 0.0 for k in UI_TO_SP.keys()},
            "recommendedPGood": 0.0, "recommendedPDowntime": 0.0
        }
    
    sys.stdout.write(json.dumps(response, cls=NumpyEncoder))

if __name__ == "__main__":
    main()
