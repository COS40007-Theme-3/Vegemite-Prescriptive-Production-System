# Theme3 — Data inventory: folders, files, and usage (Train / Inference / Test)

## Tổng quan vai trò

| Vai trò | Ý nghĩa |
|--------|----------|
| **Train** | Dữ liệu dùng để huấn luyện model (có nhãn quality hoặc downtime). |
| **Test** | Trong dataset **không có** file test riêng; test = phần tách ra từ cùng nguồn train (split 80/20 hoặc time-based). |
| **Inference** | Khi chạy app: dữ liệu đầu vào mới (sensor + SP) đưa vào model đã train để dự đoán quality / risk downtime. Có thể lấy từ SCADA, Infinity, Weekly sau khi map về cùng schema. |

---

## 1. Cấu trúc thư mục

```
Theme3/
├── data_02_07_2019-26-06-2020/   ← Production (1 năm)
├── Downtime/                      ← Log dừng máy (2 tháng)
├── Infinity Data 01_05_20 - 30_06_20/
└── Weekly Data 18_05_20 - 22_05_20/
```

---

## 2. data_02_07_2019-26-06-2020/

Dữ liệu production ~1 năm (Jul 2019 – Jun 2020). Cột chung: **VYP batch**, **Part** (loại men), **Set Time**, **7 cột SP**, **~23 cột sensor** (FFTE, TFE, Extract Tank).

### 2.1. File dùng để TRAIN (và tách Test từ đây)

| File | Chứa gì | Train / Test |
|------|---------|---------------|
| **good.csv** | Các dòng production có chất lượng **good** (solid consistency tốt). | **Train + Test:** toàn bộ data split theo time hoặc random; không có file test riêng. |
| **low bad.csv** | Các dòng có chất lượng **low_bad**. | Cùng nguồn → train/test split. |
| **high bad.csv** | Các dòng có chất lượng **high_bad**. | Cùng nguồn → train/test split. |

**Cách dùng trong notebook:** Load 3 file → gán nhãn quality theo tên file → preprocessing → **split** (vd. 80% train+val, 20% test theo thời gian hoặc stratified). **Train** = dùng để fit model; **Test** = phần hold-out để đánh giá, không phải file riêng.

### 2.2. File phụ trong cùng folder (không dùng trong pipeline chính)

| File | Chứa gì | Dùng để |
|------|---------|---------|
| **output_log.csv** | 2 cột: **VYP batch**, **Run** (good / high_bad / low_bad). ~680 batch. | Tra cứu nhãn theo batch; có thể dùng để kiểm chứng hoặc gán nhãn thay tên file. Không dùng train/test trong nb hiện tại. |
| **set_points_7_list_good_all.csv** (và list_low_bad_all, list_high_bad_all) | Chỉ 7 SP + VYP batch, Part, Employee, Set Time. Không có sensor. | Phân tích SP theo quality; không dùng trong pipeline train. |
| **set_points_7_list_all.csv** | 7 SP + cột **Class** (đã gộp 3 quality). | Có thể train model “chỉ từ SP”; không dùng trong nb chính. |
| **set_points_7_*_unique.csv** (good/low_bad/high_bad) | Long format: Machine, Process, Set Time, Value (1 dòng = 1 tham số SP). | Phân tích SP theo thời gian; không dùng train. |
| **set_points_7_mixed_*.csv** | Long format gộp nhiều quality. | So sánh SP good vs bad; không dùng train. |
| **set_points_7_*_all.csv** (good_all, low_bad_all, high_bad_all) | Dạng list SP (nhiều dòng trùng batch/time). | Biến thể của raw; không dùng trong nb. |
| **set_points_7_with_process_all.csv** | Wide: 7 SP + toàn bộ sensor + **Class**. Giống 3 file raw đã gộp. | Có thể thay 3 file good/low bad/high bad bằng 1 file này; nb hiện tại dùng 3 file riêng. |

---

## 3. Downtime/

| File | Chứa gì | Train / Test / Inference |
|------|---------|---------------------------|
| **Yeast Prep DT 04_05_20 - 01_07_20.csv** | Production Date, Time, **Cause Category**, **Cause** (TFE Low Solids, Seal Water, Sanitation…), Total Time Mins, Freq, Comments. Log sự cố dừng máy (May–Jul 2020). | **Train:** Dùng để gán nhãn binary “có downtime” theo ngày → merge với production trong khoảng May–Jun 2020 → train model Task 2. **Test:** Có thể tách val theo time trong khoảng này. **Inference:** App nhận sensor+SP mới → model dự đoán risk downtime; không cần file này lúc inference. |

---

## 4. Infinity Data 01_05_20 - 30_06_20/

| File | Chứa gì | Train / Test / Inference |
|------|---------|---------------------------|
| **Infinity_Paste Production 0105 - 3106.csv** | Part, Process, Employee, Date, Time, **VYP - Auto Batch**, VYP - Total Weight, **VYP - Solids**, VYP - Yeast Weight, VYP - Body, Comment. | **Không dùng train/test** trong nb. **Inference:** Có thể dùng làm nguồn input khi chạy app (paste production); cần map/aggregate về cùng schema (batch, Part, SP/sensor hoặc bổ sung feature solids, weight) rồi đưa vào model. |
| **Infinity_Yeast Processing 0105 - 3106.csv** | Nhiều cột (VFX, VYA, VMBX: feed, cream, residue, settings…). Part, Date, Time, batch. | **Không dùng train/test** trong nb. **Inference:** Có thể dùng làm input khi chạy app (yeast processing); cần map về schema model. |
| **Infinity Data 0105 - 310620.xlsx** | Có thể là export/phiên bản khác của dữ liệu Infinity. | Tùy nội dung; thường không dùng trong pipeline nếu đã có CSV. |

---

## 5. Weekly Data 18_05_20 - 22_05_20/

| File | Chứa gì | Train / Test / Inference |
|------|---------|---------------------------|
| **FFTE Trend 22_06 - 26_06.csv** | Time-series theo giây. Time + cột RSLinx: FFTE Steam Pressure (PV), Setpoint, Pre/Post Heat Temperatures, CIP/Product Supply Flow. Encoding thường UTF-16. | **Không dùng train/test** trong nb. **Inference:** Có thể dùng làm nguồn input khi chạy app (FFTE); aggregate theo phút/giờ hoặc theo batch rồi map về schema (SP + sensor) để đưa vào model. |
| **Evaporator Trends 18_05 - 22_05.csv** | Time-series. Time + cột VEG_* (flow PV/SP, level, density…). | Tương tự — **Inference** nếu app nhận trend; cần aggregate và map schema. |

---

## 6. Bảng tóm tắt: Train / Test / Inference

| Nguồn | Train | Test | Inference (chạy app) |
|-------|-------|------|----------------------|
| **good.csv, low bad.csv, high bad.csv** | Có — toàn bộ sau khi split (phần train+val). | Có — phần hold-out từ cùng 3 file (split 20% hoặc theo time). | Không — đây là data lịch sử đã có nhãn. |
| **Downtime (Yeast Prep DT …)** | Có — gán nhãn “có downtime” theo ngày cho production trong May–Jun 2020. | Có — phần val/test trong khoảng thời gian đó (split theo time). | Không — chỉ dùng lúc train để tạo nhãn. |
| **output_log, set_points_7_*** | Không dùng trong nb chính. | Không. | Không. |
| **Infinity (Paste, Yeast)** | Không. | Không. | Có thể — làm input cho app sau khi map/aggregate. |
| **Weekly (FFTE, Evaporator)** | Không. | Không. | Có thể — làm input cho app sau khi map/aggregate. |

---

## 7. Một dòng

- **Train:** good.csv + low bad.csv + high bad.csv (phần train+val) + Downtime (để gán nhãn Task 2).
- **Test:** Cùng 3 file production + cùng Downtime; test = phần tách ra (split), không có file test riêng.
- **Inference:** Data mới (sensor + SP) — có thể từ SCADA, hoặc từ Infinity/Weekly sau khi map về cùng schema; không dùng file good/low bad/high bad hay Downtime làm input lúc chạy app.
