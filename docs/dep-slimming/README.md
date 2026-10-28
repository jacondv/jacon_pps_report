# Giảm gói phụ thuộc & tăng tốc khởi động — Tài liệu bàn giao

Tài liệu điều hướng cho agent code. Đọc hết file này trước, rồi làm theo
[PLAN.md](PLAN.md) từng phase. Kiểm thử thủ công theo [CHECKLIST.md](CHECKLIST.md).

---

## 1. Bối cảnh

- Bản build PyInstaller (onedir) hiện nặng **907 MB / 3.276 file** trong `dist/Jacon PPS Report/`.
- Lần chạy đầu trên máy mới rất chậm: Windows Defender quét từng DLL/.pyd khi được nạp,
  exe chưa ký số. Số file và dung lượng là nguyên nhân chính.
- Code ứng dụng chỉ ~7.550 dòng (`src/pps/`), nhưng kéo theo nhiều gói nặng chỉ dùng cho
  1–2 việc nhỏ.

### Dung lượng `_internal/` theo gói (đo 2026-10-28)

| Gói | MB | Dùng ở đâu trong `src/` | Quyết định |
|---|---|---|---|
| `vtk.libs` + `vtkmodules` | 313 | Viewer 3D (pyvista / pyvistaqt / vtk) | **Giữ**, chỉ lọc module (Phase 5) |
| `open3d` | 183 | Chỉ BPA surface area: `core/surface_area.py`, `core/calculator.py` (`_to_open3d_pointcloud`), `core/analysis.py` (`compute_area_m2`) | **Bỏ** (Phase 3) |
| `dash` + `plotly` + `jedi` | 48 | Không dùng — open3d kéo theo | Tự mất khi bỏ open3d; thêm vào `excludes` |
| `scipy` + `scipy.libs` | 78 | **Không có import nào** — chỉ nằm trong `hiddenimports` của `build.spec` | **Bỏ** (Phase 1). Ngoại lệ: Phase 3 có thể dùng `scipy.spatial` nếu chọn phương án B |
| `report/` (wkhtmltopdf ~40 MB + assets) | 80 | `report/core/html_pdf_generator.py` | **Giữ** trong đợt này (xem §5 "Ngoài phạm vi") |
| `matplotlib` | 12 | `render/picking.py` (`Path.contains_points`), `report/core/html_pdf_generator.py` (1 biểu đồ cột) | **Bỏ** (Phase 2) |
| `PIL` | 13 | Pyvista cần (screenshot) | Giữ |
| `reportlab` | — | **Không dùng** (chỉ còn `.pyc` cũ trong `report/**/__pycache__`) | **Bỏ** (Phase 1) |
| `PySide6` | 103 | Toàn bộ UI | Giữ, loại module Qt không dùng (Phase 5) |

Môi trường hiện tại (`.venv`): Python 3.10.11, PySide6 6.11.2, pyvista 0.47.3, pyvistaqt 0.11.4,
vtk 9.6.1, numpy 2.2.6, open3d 0.19.0, scipy 1.15.3, matplotlib 3.10.8, PyInstaller 6.20.0.

---

## 2. Mục tiêu & tiêu chí hoàn thành

1. **Mọi chức năng như cũ**: mở PLY, hiển thị 3D, chọn vùng (rectangle/polygon/lasso),
   đo khoảng cách, đo diện tích, ghi chú, layer, undo/redo, lưu/mở `.ppsproj`,
   xuất PDF, User Guide. Toàn bộ `pytest` xanh.
2. **Số liệu không đổi**, trừ diện tích/thể tích ở Phase 3 (xem §3 quy tắc 4).
3. **Gỡ khỏi bản build**: `open3d`, `scipy` (trừ khi Phase 3 chọn phương án B), `matplotlib`,
   `reportlab`, `dash`, `plotly`, `jedi`.
4. **Mục tiêu đo được** (ghi số vào [PLAN.md §Nhật ký đo](PLAN.md#nhật-ký-đo)):
   - Dung lượng `dist/` ≤ **450 MB** sau Phase 1–4, cố gắng ≤ **350 MB** sau Phase 5.
   - Số file trong `dist/` giảm ≥ 40 %.
   - Thời gian từ double-click đến cửa sổ hiện ra (cold start, lần đầu sau khi copy
     sang thư mục mới) giảm rõ rệt so với baseline.

---

## 3. Quy tắc bắt buộc cho agent

1. **Chỉ làm việc trên nhánh `perf/slim-deps`.** Không commit lên `main`, `dev/v2.0`, `office`.
2. **Mỗi phase = 1 hoặc vài commit nhỏ, tự đứng được** (test xanh sau mỗi commit). Cuối mỗi
   phase tạo tag `slim/phase-N-done`. Như vậy có thể rollback từng phase riêng.
3. **Không sửa `tests/golden/sample_baseline.json`** ở Phase 1, 2, 4, 5. Golden test
   (`tests/test_calculator_golden.py`) phải xanh nguyên vẹn với `rel=1e-9`.
4. **Phase 3 đổi thuật toán diện tích → số diện tích/thể tích sẽ lệch.** Đây là thay đổi số
   liệu duy nhất được phép, và **phải dừng lại xin chủ dự án duyệt** bảng so sánh trước khi
   cập nhật golden. Không tự ý merge Phase 3.
5. Giữ nguyên các hành vi "trông giống bug" đã ghi trong `docs/REFACTOR_PLAN.md` §7.1,
   đặc biệt: `calculate_area_and_volume()` **sửa `distances` tại chỗ** (|d|<12 và |d|>500 → 0)
   và `calculate_thickness_distribution()` chạy trên chính mảng đã sửa đó.
6. Không đổi giao diện, phím tắt, key trong `ctx` của report, template HTML (trừ chỗ chèn
   biểu đồ ở Phase 2).
7. Commit message viết bằng tiếng Anh, ngắn gọn. **Không** thêm dòng `Co-Authored-By`,
   "Generated with …" hay bất kỳ ghi công AI nào.
8. Không thêm file `.bat` / `.vbs` launcher.
9. Gặp quyết định ngoài tài liệu này (đổi số liệu, đổi UI, thêm dependency mới) → dừng và hỏi.

---

## 4. Rollback

### 4.1 Điểm mốc đã tạo sẵn

| Mốc | Ý nghĩa |
|---|---|
| tag `baseline/pre-slim-deps` | `main` tại thời điểm bắt đầu — trạng thái chạy tốt cuối cùng |
| nhánh `perf/slim-deps` | Nhánh làm việc, tách từ `main` |
| tag `slim/phase-N-done` | Do agent tạo cuối mỗi phase |

### 4.2 Trước khi bắt đầu (Phase 0 — bắt buộc)
- Nén bản build đang chạy được: `dist/Jacon PPS Report/` → `installer_output/baseline-pre-slim.zip`
  (thư mục này đã nằm trong `.gitignore`). Giữ lại cả file installer `.exe` hiện có nếu có.
- Xuất danh sách gói: `.venv\Scripts\python -m pip freeze > docs/dep-slimming/requirements-baseline.lock`
  và commit file này → có thể dựng lại đúng `.venv` cũ.

### 4.3 Các tình huống rollback

| Tình huống | Lệnh |
|---|---|
| Bỏ toàn bộ đợt chuyển đổi | `git switch main` — `main` không bị đụng tới. Xoá nhánh nếu muốn: `git branch -D perf/slim-deps` |
| Bỏ từ phase N trở đi, giữ các phase trước | `git switch perf/slim-deps && git reset --hard slim/phase-<N-1>-done` |
| Bỏ riêng 1 phase đã merge vào `main` | `git revert <commit…>` của phase đó (vì mỗi phase là commit riêng) |
| Dựng lại `.venv` cũ | `python -m venv .venv-old && .venv-old\Scripts\pip install -r docs/dep-slimming/requirements-baseline.lock` |
| Cần gửi bản cũ cho người dùng ngay | Giải nén `installer_output/baseline-pre-slim.zip` |

Lưu ý: **không gỡ gói khỏi `.venv` hiện tại** cho tới Phase 6. Gỡ trong `requirements.txt` và
`build.spec` trước; thử "không có gói" bằng venv sạch riêng (`.venv-slim`, xem PLAN Phase 6).
Như vậy `.venv` cũ vẫn chạy được nhánh `main` bất cứ lúc nào.

### 4.4 Merge về `main`
Chỉ khi: toàn bộ test xanh, CHECKLIST.md thủ công đạt, bản build đã chạy thử trên ít nhất
1 máy sạch, chủ dự án duyệt. Dùng merge commit (`git merge --no-ff perf/slim-deps`) để có thể
revert cả đợt bằng một lệnh `git revert -m 1 <merge-commit>`.

---

## 5. Ngoài phạm vi đợt này
- Chuyển sang C# / framework UI khác.
- Thay wkhtmltopdf (tiết kiệm ~40 MB nhưng phải viết lại template; để đợt sau).
- Nuitka (có thể thử sau khi xong Phase 6, trên nhánh riêng).
- Ký số code signing: cần chứng thư của công ty — agent chỉ chuẩn bị bước `signtool` trong
  tài liệu build nếu được cung cấp chứng thư, không tự mua/tạo.
