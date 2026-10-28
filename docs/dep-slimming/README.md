# Tăng tốc khởi động & giảm gói phụ thuộc (giữ open3d) — Tài liệu bàn giao

Tài liệu điều hướng cho agent code. Đọc hết file này trước, rồi làm theo
[PLAN.md](PLAN.md) từng phase. Kiểm thử thủ công theo [CHECKLIST.md](CHECKLIST.md).

**Phương án đã chốt (2026-10-28): giữ open3d** — số liệu diện tích/thể tích trong báo cáo
phải giữ **y nguyên**. Phương án bỏ open3d (Delaunay VTK) chỉ là dự phòng, xem
[PLAN.md §Phụ lục](PLAN.md#phụ-lục--phương-án-dự-phòng-bỏ-open3d) — **không làm trong đợt này**.

---

## 1. Bối cảnh

- Bản build PyInstaller (onedir) nặng **907 MB / 3.276 file** (`dist/Jacon PPS Report/`).
- Lần chạy đầu rất chậm vì Windows Defender quét từng DLL/.pyd **khi được nạp**. Cache quét
  **mất sau mỗi lần khởi động lại máy** → loại trừ thư mục khỏi Defender không giải quyết
  được (đã thử). Cách duy nhất: **nạp ít file hơn lúc khởi động** và làm bản build nhỏ hơn.

### Nguyên nhân đo được (2026-10-28)

| Phát hiện | Số đo |
|---|---|
| 7 file trong `src/pps/render/` dùng `import vtk` → nạp **toàn bộ 153 module VTK** (vtkWebCore, vtkIOLSDyna, vtkIOOggTheora, vtkAcceleratorsVTKmFilters …) dù chỉ dùng 15 class | pyvista + pyvistaqt chỉ cần **62** module |
| Import `pps.ui.main_window` lần đầu (Defender chưa quét, `.venv`) | **288 s**, gần hết nằm trong `import vtk` |
| Import `pps.ui.main_window` các lần sau | 2,6–3,4 s |
| `matplotlib` (+ PIL) bị nạp lúc khởi động qua `render/picking.py` | |
| `jinja2`, `pdfkit` bị nạp lúc khởi động qua `ui/main_window.py:31` → `pps.report` | |
| `open3d` **không** nạp lúc khởi động (đã import trong hàm) — nhưng `import open3d` mất 3,3 s (warm) và kéo theo `dash`, `plotly` → làm chậm **lần Calculate đầu tiên** | |

### Dung lượng `_internal/` theo gói

| Gói | MB | Dùng ở đâu | Quyết định |
|---|---|---|---|
| `vtk.libs` + `vtkmodules` | 313 | Viewer 3D | Giữ; chỉ nạp/đóng gói module cần (Phase 1, 4) |
| `open3d` | 183 (`cpu/` 145, `resources/` 38) | BPA surface area | **Giữ**. Thử bỏ `resources/`, `nbextension/`, `labextension/`, `examples/` (Phase 4) |
| `dash` + `plotly` + `jedi` | 48 | Không dùng — `import open3d` kéo theo | Giữ những gói `import open3d` thực sự nạp; loại phần còn lại (Phase 4) |
| `scipy` | 78 | **Không có import nào** | **Bỏ** (Phase 4) |
| `report/` (wkhtmltopdf ~40 MB) | 80 | Xuất PDF | Giữ |
| `matplotlib` | 12 | `picking.py`, biểu đồ PDF | **Bỏ** (Phase 3) |
| `reportlab` | — | **Không dùng** | **Bỏ** (Phase 4) |
| `PySide6` | 103 | UI | Giữ, loại module Qt không dùng (Phase 4) |
| `PIL` | 13 | pyvista cần | Giữ |

Môi trường `.venv`: Python 3.10.11, PySide6 6.11.2, pyvista 0.47.3, pyvistaqt 0.11.4,
vtk 9.6.1, numpy 2.2.6, open3d 0.19.0, PyInstaller 6.20.0.

---

## 2. Mục tiêu & tiêu chí hoàn thành

1. **Mọi chức năng như cũ**: mở PLY, hiển thị 3D, chọn vùng, đo khoảng cách/diện tích, ghi chú,
   layer, undo/redo, lưu/mở `.ppsproj`, xuất PDF, User Guide. Toàn bộ `pytest` xanh.
2. **Số liệu không đổi**: `tests/test_calculator_golden.py` xanh nguyên vẹn (`rel=1e-9`) ở mọi
   phase. Không được sửa `tests/golden/sample_baseline.json`.
3. **Khởi động**: số module `vtkmodules.vtk*` nạp lúc mở cửa sổ ≤ 70 (từ 153); không nạp
   `matplotlib`, `jinja2`, `pdfkit`, `open3d` trước khi cửa sổ hiện.
4. **Đo được** (ghi vào [PLAN.md §Nhật ký đo](PLAN.md#nhật-ký-đo)):
   - Cold start (đo ngay sau khi **khởi động lại máy**) giảm rõ rệt so với baseline.
   - Dung lượng `dist/` ≤ 750 MB, số file giảm ≥ 25 %.
   - Lần Calculate đầu tiên không chậm hơn các lần sau quá 1 s (nhờ nạp sẵn open3d ở nền).
5. **Không thêm gói mới.** Mọi công cụ/thư viện phải miễn phí cho dùng thương mại/nội bộ
   (công ty không có license Visual Studio → không dùng MSVC, không viết extension C/C++).

---

## 3. Quy tắc bắt buộc cho agent

1. **Chỉ làm việc trên nhánh `perf/slim-deps`.** Không commit lên `main`, `dev/v2.0`, `office`.
2. **Mỗi phase = 1 hoặc vài commit nhỏ, tự đứng được** (test xanh sau mỗi commit). Cuối mỗi
   phase tạo tag `slim/phase-N-done` → rollback được từng phase.
3. **Không đổi thuật toán tính toán** (`core/calculator.py`, `core/surface_area.py`,
   `core/analysis.py` chỉ được đổi vị trí import, không đổi logic). Giữ các hành vi trong
   `docs/REFACTOR_PLAN.md` §7.1 (đặc biệt: `distances` bị sửa tại chỗ).
4. Không đổi giao diện, phím tắt, key `ctx` của report, template HTML.
5. Commit message tiếng Anh, ngắn gọn. **Không** thêm `Co-Authored-By`, "Generated with …" hay
   bất kỳ ghi công AI nào.
6. Không thêm file `.bat` / `.vbs` launcher.
7. Không gỡ gói khỏi `.venv` hiện tại — thử "không có gói" bằng venv riêng `.venv-slim` (Phase 5).
8. Gặp quyết định ngoài tài liệu này (đổi số liệu, đổi UI, thêm dependency) → dừng và hỏi.

---

## 4. Rollback

### 4.1 Điểm mốc

| Mốc | Ý nghĩa |
|---|---|
| tag `baseline/pre-slim-deps` | `main` lúc bắt đầu — trạng thái chạy tốt cuối cùng |
| nhánh `perf/slim-deps` | Nhánh làm việc |
| tag `slim/phase-N-done` | Agent tạo cuối mỗi phase |

### 4.2 Trước khi bắt đầu (Phase 0 — bắt buộc)
- Nén bản build đang chạy được: `dist/Jacon PPS Report/` → `installer_output/baseline-pre-slim.zip`
  (đã nằm trong `.gitignore`). Giữ lại installer `.exe` hiện có nếu có.
- `pip freeze > docs/dep-slimming/requirements-baseline.lock` và commit → dựng lại được `.venv` cũ.

### 4.3 Các tình huống

| Tình huống | Lệnh |
|---|---|
| Bỏ toàn bộ đợt này | `git switch main` (main không bị đụng). Xoá nhánh nếu muốn: `git branch -D perf/slim-deps` |
| Bỏ từ phase N trở đi | `git switch perf/slim-deps && git reset --hard slim/phase-<N-1>-done` |
| Bỏ riêng 1 phase đã merge | `git revert <các commit của phase>` |
| Dựng lại `.venv` cũ | `python -m venv .venv-old && .venv-old\Scripts\pip install -r docs/dep-slimming/requirements-baseline.lock` |
| Cần gửi bản cũ ngay | Giải nén `installer_output/baseline-pre-slim.zip` |

### 4.4 Merge về `main`
Chỉ khi: test xanh, CHECKLIST.md đạt trên exe, đã đo cold start sau khi khởi động lại máy,
chủ dự án duyệt. Dùng `git merge --no-ff perf/slim-deps` để revert cả đợt bằng
`git revert -m 1 <merge-commit>`.

---

## 5. Ngoài phạm vi
- Bỏ open3d / đổi thuật toán diện tích (dự phòng, xem PLAN.md Phụ lục).
- Loại trừ thư mục khỏi Defender (không hiệu quả — mất sau mỗi lần khởi động lại máy).
- Thay wkhtmltopdf; Nuitka; chuyển sang C#.
- Ký số code signing: chỉ ghi chú bước `signtool` nếu chủ dự án cung cấp chứng thư.
