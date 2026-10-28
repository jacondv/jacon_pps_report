# Báo cáo kết quả — tăng tốc khởi động & giảm gói (giữ open3d)

Nhánh `perf/slim-deps`, ngày 2026-10-28. **Chưa merge** — chờ chủ dự án kiểm thử thủ công
([CHECKLIST.md](CHECKLIST.md)) và đo cold start sau khi khởi động lại máy.

## Kết quả

| | Baseline | Sau cùng (build từ `.venv-slim`) |
|---|---|---|
| Dung lượng `dist/` | 900 MB | **722 MB** (−20 %) |
| Số file `dist/` | 3 277 | **1 747** (−47 %) |
| Bộ cài | 204 MB | **159 MB** (−22 %) |
| Module VTK nạp lúc mở cửa sổ | 153 | **36** (venv-slim) / 62 (`.venv` cũ) |
| Khởi động warm (đến khi cửa sổ được vẽ) | ~3.3 s ¹ | **1.87 s** |
| Lần chạy đầu ngay sau build (file mới, Defender chưa quét) | 14.65 s ¹ | **7.55 s** |
| Splash xuất hiện sau khi tạo QApplication | — | ~10 ms |
| open3d nạp lần đầu | khi bấm Calculate | ở nền, 1.4–2.3 s sau khi cửa sổ hiện |
| Số liệu tính toán | | **Giống hệt** (golden test `rel=1e-9` pass trên cả 2 venv) |
| Test | 131 | **138** pass |

¹ Baseline đo đến mốc log "MainWindow shown", mốc này **sớm hơn** lúc cửa sổ được vẽ thật,
nên mức cải thiện thực tế còn lớn hơn bảng.

**Cold start thật (sau khi khởi động lại máy) chưa đo** — cần chủ dự án làm, xem dưới.

## Đã làm

| Phase | Nội dung chính | Tag |
|---|---|---|
| 0 | Baseline, lock `requirements-baseline.lock`, `tools/measure_startup.py`, `tools/startup_modules.py`. Sửa test treo do hộp thoại "chưa lưu" | `slim/phase-0-done` |
| 1 | `import vtk` → import theo từng `vtkmodules.*` (7 file render + test); `render/vtk_setup.py`; test chống tái phát | `slim/phase-1-done` |
| 2 | Report (jinja2/pdfkit) nạp khi xuất PDF; splash; open3d nạp ở nền (`app/preload.py`) | `slim/phase-2-done` |
| 3 | **Huỷ** — pyvista bắt buộc matplotlib | — |
| 4 | Build chỉ gói module dùng thật (hook VTK/pyvista), bỏ scipy, `open3d/resources`, VTK-m; `console=False`, `upx=False`; `tools/check_bundle.py` | `slim/phase-4-done` |
| 5 | Venv sạch, `requirements-build.lock`, bỏ 5 500 file stub của jedi, bộ cài xoá bản cũ khi nâng cấp | (chưa tag) |

## Lỗi tìm thấy và đã sửa dọc đường
1. **matplotlib dựng lại cache font mỗi lần mở exe** (PyInstaller đặt `MPLCONFIGDIR` vào thư mục
   tạm, xoá khi thoát) → nay cache ở `%LOCALAPPDATA%\TunnelAnalyzer\matplotlib`.
2. **`QSplashScreen.show()` chặn ~1 s** trên Windows → splash dùng `QLabel`.
3. **Xuất PDF sẽ lỗi khi tắt console**: pdfkit `verbose=True` ghi ra `sys.stdout` (= `None`) →
   `verbose=False`; có test chạy export với `sys.stdout=None`.
4. **Test smoke treo** khi document "chưa lưu" lúc teardown (hộp thoại modal) → `before_close_func`.

## Cần chủ dự án làm trước khi merge
1. **Kiểm thử thủ công** trên `dist\Jacon PPS Report\Jacon PPS Report.exe` theo [CHECKLIST.md](CHECKLIST.md)
   — đặc biệt: chữ trên legend/nhãn 3D, chọn vùng, Measure Area, Calculate, **xuất PDF**, User Guide.
   (Agent đã kiểm tra tự động: đủ module, khởi động, preload open3d, đóng app sạch — nhưng không
   bấm thử được giao diện.)
2. **Đo cold start**: khởi động lại máy → mở terminal ở repo →
   `.venv\Scripts\python tools\measure_startup.py "dist\Jacon PPS Report\Jacon PPS Report.exe"`.
   Lần khởi động lại khác: giải nén `installer_output\baseline-pre-slim.zip` ra thư mục mới, đo exe
   cũ bằng cùng lệnh (bản cũ không có dòng "window painted" → sửa tạm `READY_MARKER` thành
   `"MainWindow shown"` cho lần đo đó). Ghi vào PLAN.md §Nhật ký.
3. **Quyết định**:
   - Số phiên bản: bộ cài mới vẫn là 3.0.0 (trùng tên bản cũ) — nên tăng `MyAppVersion` trong `installer.iss`.
   - `installer.iss` vẫn có tuỳ chọn thêm loại trừ Defender — đã xác nhận không hiệu quả sau khi
     khởi động lại máy; giữ hay bỏ là quyết định của chủ dự án.
   - Build bản phát hành từ `.venv-slim` (`requirements-build.lock`: open3d 0.20, pyvista 0.49,
     vtk 9.7, PySide6 6.12) hay từ `.venv` cũ (open3d 0.19, pyvista 0.47, vtk 9.6). Cả hai qua đủ test;
     bản `.venv-slim` nhẹ hơn (36 module VTK).
4. Merge: `git switch main && git merge --no-ff perf/slim-deps` (rollback: README §4).

## Sự cố trong lúc làm
- `installer_output\Jacon PPS Report Setup 3.0.0.exe` bản cũ **bị ghi đè** khi dựng bộ cài mới
  (Phase 0 chỉ sao lưu `dist/`). Đã dựng lại từ `baseline-pre-slim.zip` + `installer.iss` ở tag
  `baseline/pre-slim-deps` → `installer_output\Jacon PPS Report Setup 3.0.0 (baseline pre-slim).exe`
  (cùng nội dung, khác byte).
- `sample\...cloud_compared_07.ppsproj` (không commit) do lần chạy test bị treo đầu tiên tạo ra
  khi hộp thoại "chưa lưu" được bấm Save — có thể xoá.
