# So sánh phương pháp tính diện tích thay open3d BPA

Thí nghiệm ngày 2026-10-28 trên `sample/2_thickness_01#20260203_093652#cloud_compared_07.ply`
(202.339 điểm; vòm hầm ~6.9 × 5.7 × 5.1 m, bán kính fit ~2.9 m). Máy dev 22 luồng.
Tham chiếu: `pps.core.surface_area.surface_area` hiện tại (open3d 0.19, radii 0.05/0.1).
Tập "đạt target > X mm": điểm có `d > X` sau khi clip |d|<12 và |d|>500 về 0, giống
`calculate_area_and_volume`. Giá trị open3d cho > 40 và > 50 mm trùng golden baseline.

## Kết luận
Chọn **Delaunay 2D của VTK theo khối 1 m, R_MAX = 0.07 m** ([reference_area.py](reference_area.py)):
lệch −1.0 % … +1.6 % so với open3d, nhanh ~2.6×, không thêm gói nào, toàn bộ miễn phí.
Cần kiểm chứng thêm trên file PLY thật khác trước khi áp dụng (PLAN.md Phase 3.3).

## 1. Thời gian từng bước của open3d (toàn bộ cloud)

| Bước | Thời gian |
|---|---|
| voxel_down_sample | 0.10 s |
| remove_radius_outlier | 0.15 s |
| estimate_normals | 0.11 s |
| orient_normals_consistent_tangent_plane | **7.98 s** |
| BPA | 3.13 s |
| Tổng | 12.4 s → 99.748 m², 224.771 tam giác |

## 2. Các phương án đã thử

| Phương án | Toàn bộ cloud | Thời gian | Lý do loại / chọn |
|---|---|---|---|
| BPA viết bằng Python + numpy (prototype) | 103.902 (+4.2 %) | 67 s | Quá chậm |
| BPA numpy chia khối 2 m + multiprocessing 4 / 8 / 16 tiến trình | 103.852 | 37 / 26 / 20 s | Vẫn chậm hơn open3d trên máy phổ thông |
| Port BPA sang C++ (pybind11) | — (không làm) | ~2–5 s (ước tính) | Cần MSVC, công ty không có license |
| Đếm ô lưới trên mặt phẳng chiếu | 64.6 … 97.7 (−35 % … −2 %) | 0.4–1.4 s | Phụ thuộc mạnh vào cỡ ô |
| Delaunay trên **1 mặt phẳng** cho cả cloud | 47.0 (−52.9 %) | — | Vòm hầm bị gập khi chiếu |
| Delaunay trên mặt trụ trải phẳng (không chia khối) | 102.18 (+2.4 %) | 8.8 s | Chỉ đúng với hầm hình trụ |
| Delaunay khối 2 m, có hiệu chỉnh normal | 91.7 (−8 %) | — | Làm phẳng cả độ gồ ghề thật |
| Delaunay khối 2 m, R 0.07 | 97.992 (−1.8 %) | 1.4 s | Tốt, nhưng khối 1 m tốt hơn |
| **Delaunay khối 1 m, R 0.07** | **98.727 (−1.0 %)** | **~4.4 s** | **Chọn** |

## 3. Quét tham số Delaunay (lệch so với open3d)

| Tập điểm | open3d | 2 m R.06 | 2 m R.07 | 2 m R.08 | 1 m R.06 | **1 m R.07** | 1 m R.08 |
|---|---|---|---|---|---|---|---|
| Toàn bộ | 99.748 | −2.9 % | −1.8 % | −0.5 % | −2.2 % | **−1.0 %** | +0.1 % |
| > 20 mm | 16.588 | −1.6 % | +1.2 % | +3.6 % | −1.8 % | **+1.1 %** | +3.4 % |
| > 40 mm | 14.154 | 0.0 % | +2.1 % | +4.2 % | −0.5 % | **+1.3 %** | +3.1 % |
| > 50 mm | 13.775 | −0.6 % | +1.8 % | +4.0 % | −1.1 % | **+1.1 %** | +3.0 % |
| > 100 mm | 11.727 | 0.0 % | +1.7 % | +3.3 % | −0.1 % | **+1.6 %** | +3.3 % |

Không có R nào khớp cả hai loại tập: toàn bộ cloud khớp nhất ở R ≈ 0.08, tập đạt target (rời rạc,
mép lởm chởm — Delaunay lấp khe < R mà BPA để trống) khớp nhất ở R ≈ 0.06. R = 0.07 cân bằng.
R = 0.07 mới được chỉnh trên **1 file** — phải kiểm chứng trên file khác.

## 4. Dữ liệu tổng hợp (reference_area.py, khối 1 m, R 0.07)

| Ca | Đúng | Delaunay | open3d | Dịch gốc +0.3 m |
|---|---|---|---|---|
| Nửa trụ R 3 m, dài 2 m, nhiễu 3 mm | 18.850 | 19.388 (+2.9 %) | 19.043 (+1.0 %) | 0.00 % |
| Mặt phẳng 2×3 m có lỗ R 0.5 m, nhiễu 3 mm | 5.215 | 5.482 (+5.1 %) | 5.214 (0.0 %) | +0.53 % |

Delaunay đếm cả độ gồ ghề của nhiễu (BPA "lăn" trên đỉnh nên mượt hơn) → cao hơn trên mặt phẳng
nhiễu. Trên dữ liệu hầm thật, hiệu ứng này gần như bù với việc Delaunay lấp ít khe hơn ở mép.

## 5. Rủi ro đã biết
- Khối chứa 2 mặt chồng nhau theo hướng chiếu (góc nền–vách, hầm bán kính < ~1.5 m, cloud 2 lớp)
  có thể nối sai tam giác. Khối 1 m giảm rủi ro so với 2 m.
- Kết quả phụ thuộc nhẹ vào gốc lưới khối (±0.5 % trên mặt phẳng tổng hợp).

## 6. Kiểm chứng trên dữ liệu thật
*(Agent điền ở Phase 3.3 — bảng theo từng file PLY do chủ dự án cung cấp.)*
