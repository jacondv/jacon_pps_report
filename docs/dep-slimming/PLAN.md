# Kế hoạch thực hiện theo phase (giữ open3d)

Đọc [README.md](README.md) (quy tắc + rollback) trước. Làm **tuần tự**. Mỗi phase kết thúc bằng:

```
.venv\Scripts\python -m pytest -q        # phải xanh, gồm test_calculator_golden.py
git commit ...                            # 1 hoặc vài commit nhỏ
git tag slim/phase-N-done
```

và ghi một dòng vào [Nhật ký đo](#nhật-ký-đo) ở cuối file.

Thứ tự phase theo **tác động lên khởi động / rủi ro**: Phase 1 là việc quan trọng nhất.

---

## Phase 0 — Chuẩn bị & đo baseline

1. Xác nhận đang ở nhánh `perf/slim-deps`, working tree sạch, tag `baseline/pre-slim-deps` tồn tại.
2. `pip freeze > docs/dep-slimming/requirements-baseline.lock` → commit.
3. Nén `dist/Jacon PPS Report/` → `installer_output/baseline-pre-slim.zip` (không commit).
4. Tạo `tools/measure_startup.py` (script dev, không đóng gói):
   - Tham số: đường dẫn exe, hoặc `--source` để chạy `python main.py`; `--runs N`.
   - Ghi thời điểm khởi chạy process → chờ dòng `MainWindow shown` mới xuất hiện trong
     `%LOCALAPPDATA%\TunnelAnalyzer\logs\app.log` (log đã có sẵn, xem `main.py`) → in số giây
     → tắt process.
   - In thêm dung lượng và số file của thư mục chứa exe.
5. Tạo `tools/startup_modules.py`: import `pps.app.qt_env` rồi `pps.ui.main_window`, in số module
   `vtkmodules.vtk*` đã nạp và có/không có `matplotlib`, `jinja2`, `pdfkit`, `open3d`, `scipy`
   trong `sys.modules`. (Baseline đo được: 153 module VTK; có matplotlib, jinja2, pdfkit.)
6. Đo baseline và ghi Nhật ký:
   - `python -X importtime -c "import pps.app.qt_env, pps.ui.main_window" 2> docs/dep-slimming/importtime-baseline.txt`
     (chạy với `PYTHONPATH=src`). Ghi top 15 module chậm nhất.
   - Exe hiện tại: dung lượng, số file, khởi động warm (trung vị 3 lần).
   - **Cold start: khởi động lại máy → chạy `measure_startup.py` 1 lần ngay sau khi đăng nhập.**
     Việc này cần chủ dự án làm (agent không được tự khởi động lại máy) → agent chuẩn bị lệnh,
     ghi "chờ đo cold" nếu chưa có số. **Không bịa số.**
7. `pytest -q`, ghi số test pass.

**Commit:** `Add dependency-slimming baseline lock and startup measurement tools`

---

## Phase 1 — Chỉ nạp module VTK thực sự dùng (tác động lớn nhất)

**Bằng chứng:** `import vtk` = `vtkmodules.all` → 153 module/DLL. Code chỉ dùng 15 class.

### 1.1 Thay import trong `src/`
Thay `import vtk` + `vtk.X` bằng import trực tiếp từ module chứa class. Bảng ánh xạ (đã kiểm
tra bằng `vtk.X.__module__` trên vtk 9.6.1):

| Class | Module |
|---|---|
| `vtkActor`, `vtkActor2D`, `vtkTextActor`, `vtkBillboardTextActor3D`, `vtkPolyDataMapper`, `vtkPolyDataMapper2D`, `vtkCoordinate`, `vtkRenderer`, `vtkPointPicker` | `vtkmodules.vtkRenderingCore` |
| `vtkPolyData`, `vtkCellArray`, `vtkLine` | `vtkmodules.vtkCommonDataModel` |
| `vtkPoints` | `vtkmodules.vtkCommonCore` |
| `vtkSphereSource`, `vtkLineSource` | `vtkmodules.vtkFiltersSources` |

Các file và class đang dùng:

| File | Class |
|---|---|
| `render/actors2d.py` | vtkActor2D, vtkCellArray, vtkLine, vtkPoints, vtkPolyData, vtkPolyDataMapper2D |
| `render/color_legend.py` | vtkActor2D, vtkCellArray, vtkCoordinate, vtkLine, vtkPolyData, vtkPolyDataMapper2D, vtkTextActor |
| `render/labels.py` | vtkActor, vtkActor2D, vtkBillboardTextActor3D, vtkCellArray, vtkLine, vtkPoints, vtkPolyData, vtkPolyDataMapper, vtkPolyDataMapper2D, vtkSphereSource, vtkTextActor |
| `render/measurement_renderer.py` | vtkActor, vtkActor2D, vtkLineSource, vtkPolyDataMapper |
| `render/overlay.py` | vtkTextActor |
| `render/picking.py` | vtkPointPicker |
| `render/viewport.py` | vtkRenderer |

Kiểm tra lại bằng `grep -rnoE "\bvtk\.[A-Za-z_0-9]+" src` trước khi sửa (có thể có hằng số
`vtk.VTK_*` hoặc class mà grep ở trên chưa thấy) — mọi tên phải được ánh xạ.

### 1.2 Bảo đảm VTK vẫn render được
Không còn `import vtk` thì các module **"object factory"** (backend OpenGL, font, kiểu tương tác)
không tự được nạp. pyvista thường tự nạp chúng, nhưng phải bảo đảm chắc chắn:
- Tạo `src/pps/render/vtk_setup.py` import (chỉ để đăng ký factory, `# noqa: F401`):
  `vtkmodules.vtkRenderingOpenGL2`, `vtkmodules.vtkRenderingFreeType`,
  `vtkmodules.vtkInteractionStyle`, `vtkmodules.vtkRenderingContextOpenGL2` (nếu có trong 62
  module pyvista nạp — kiểm tra), và import nó ở đầu `render/viewport.py`.
- Chạy app từ source: cloud hiển thị, text 2D/3D (labels, legend, note) hiện đúng font,
  picking hoạt động, xoay/zoom mượt. Không có cảnh báo `vtkObjectFactory`/"no override found"
  trong console.

### 1.3 Tests
`tests/test_measurement_renderer.py`, `test_note_renderer.py`, `test_tool_manager.py` dùng
`import vtk` → đổi sang import trực tiếp (`vtkRenderer`, `vtkRenderWindow` ∈
`vtkmodules.vtkRenderingCore`, `vtkActor2D`). Test được phép dùng `import vtk`, nhưng đổi để
test chạy giống cấu hình thật.

### 1.4 Test chống tái phát
`tests/test_startup_imports.py`: chạy **subprocess** Python sạch, import `pps.app.qt_env` +
`pps.ui.main_window`, assert:
- `"vtkmodules.all"` không có trong `sys.modules`;
- số module `vtkmodules.vtk*` ≤ 70 (ghi số thực tế đo được vào comment).
(Phase 2 bổ sung assert cho matplotlib/jinja2/pdfkit/open3d.)

### 1.5 Đo
`tools/startup_modules.py` + `-X importtime` → `importtime-phase1.txt`. Ghi Nhật ký.

**Commits:** `Import only the VTK modules the renderer uses`, `Guard against importing all of VTK at startup`

---

## Phase 2 — Import trễ, splash screen, nạp sẵn open3d ở nền

### 2.1 Report chỉ nạp khi xuất PDF
- `ui/main_window.py:31` `from pps.report import PDFGenerator` → import bên trong handler xuất
  PDF (quanh dòng 796).
- `tests/test_main_window_smoke.py::test_export_pdf_produces_real_file` có monkeypatch — kiểm
  tra đường dẫn còn đúng.

### 2.2 matplotlib không nạp lúc khởi động
- `render/picking.py:13` `from matplotlib.path import Path` → tạm chuyển vào trong
  `points_in_polygon` (Phase 3 sẽ bỏ hẳn matplotlib).

### 2.3 Splash screen
- Trong `main.py`: sau `create_app()` + `apply_theme()`, **trước** `from pps.ui.main_window import
  MainWindow`, hiện `QSplashScreen` (logo từ `assets/icon.ico` hoặc ảnh có sẵn trong `assets/`,
  dòng chữ "Loading…"), gọi `app.processEvents()`.
- Di chuyển import `MainWindow` vào trong `main()` (sau splash). Giữ các import nhẹ ở đầu file.
- `splash.finish(window)` sau `window.showMaximized()`.
- Có thể cập nhật dòng chữ splash theo từng bước ("Loading 3D engine…") — chỉ dùng
  `showMessage`, không thêm logic.

### 2.4 Nạp sẵn open3d ở nền
- Sau khi cửa sổ hiện (`QTimer.singleShot(0, ...)` trong `MainWindow` hoặc `main.py`), chạy một
  `QThread` (mẫu như `app/workers.py`) chỉ làm `import open3d` (bọc try/except, log lỗi ở mức
  WARNING — lỗi ở đây không được làm hỏng app; Calculate vẫn tự import như cũ).
- Log `"open3d preloaded in %.2fs"`.
- Không thay đổi `core/` — các `import open3d` trong hàm giữ nguyên (import lần 2 lấy từ
  `sys.modules`, gần như tức thì).
- Kiểm tra: mở app → chờ log preload → mở PLY → Calculate: lần đầu không chậm hơn lần sau
  quá 1 s. Bấm Calculate **trước** khi preload xong cũng phải chạy đúng (import lock của Python
  tự xử lý — chỉ cần xác nhận).
- Đóng app khi preload đang chạy: không treo, không crash (thread phải có parent hoặc
  được `wait()` khi đóng).

### 2.5 Test chống tái phát
Bổ sung `test_startup_imports.py`: sau khi import `pps.ui.main_window`, **không** có
`jinja2`, `pdfkit`, `open3d`, `scipy` trong `sys.modules`.

**matplotlib là ngoại lệ** (phát hiện ở Phase 0): `pyvista.plotting.colors` tự
`import matplotlib.pyplot` trong `try/except ImportError` nếu môi trường có matplotlib, nên
trong `.venv` dev nó luôn bị nạp. Bản build không có matplotlib (Phase 4) thì pyvista bỏ qua.
Vì vậy test matplotlib theo kiểu khác: subprocess đặt `sys.modules["matplotlib"] = None`
(chặn import) rồi import `pps.ui.main_window` và tạo 1 `pyvista.PolyData` → phải thành công.
Phase 2 chỉ cần bảo đảm **code của `pps`** không import matplotlib ở cấp module.

**Commits:** `Defer report and matplotlib imports`, `Show a splash screen during startup`,
`Preload open3d in the background after the window is shown`

---

## Phase 3 — Bỏ matplotlib

### 3.1 `render/picking.py::points_in_polygon`
- Thay `matplotlib.path.Path(polygon).contains_points(points)` bằng numpy thuần (even-odd ray
  casting, vector hoá theo cạnh). Giữ chữ ký và nhánh `< 3 đỉnh / 0 điểm → all False`.
- Lọc trước bằng bounding box của polygon, chỉ ray-cast điểm trong bbox.
- **Test** `tests/test_picking.py`:
  - So khớp matplotlib trên 100k điểm ngẫu nhiên × (chữ nhật, polygon lõm, lasso 300 đỉnh) với
    `pytest.importorskip("matplotlib")`. Chỉ cho phép lệch với điểm cách cạnh < 1e-9 px.
  - Ca biên: polygon suy biến, mảng điểm rỗng.
  - Hiệu năng: 2 triệu điểm × lasso 300 đỉnh không chậm hơn matplotlib quá 2 lần.

### 3.2 Biểu đồ phân bố trong PDF — `report/core/html_pdf_generator.py::_create_distribution_chart`
- Vẽ bằng **QPainter → QImage → PNG** (PySide6 có sẵn), module riêng `src/pps/report/charts.py`.
- Giữ nguyên: 1200×675 px (= figsize 8×4.5 @ 150 dpi); 3 cột `< {tmin}`, `{tmin}-{tmax}`,
  `> {tmax}`; màu `#ff6060`, `#64ffa0`, `#315aff`; nhãn đỉnh cột `"{count:,}\n({percent:.0f}%)"`;
  tiêu đề "Thickness Distribution" đậm; trục X "Thickness Range (mm)", trục Y "Number of
  Points"; lưới ngang nét đứt mờ; khoảng trống trên 20 %; vạch trục Y "nice numbers"; cột 0 điểm
  vẫn có nhãn `0 (0%)`.
- Vẫn ghi file tạm `pps_report_distribution_*.png` và trả đường dẫn → **key `chart_path` và
  template HTML không đổi**.
- QImage cần `QGuiApplication` — trong app luôn có; test dùng fixture `qapp`.
- Lưu ảnh chart cũ và mới vào `docs/dep-slimming/compare/` để chủ dự án so bằng mắt.

### 3.3 Gỡ
- Xoá `matplotlib` khỏi `requirements.txt` và `hiddenimports` (`"matplotlib"`,
  `"matplotlib.backends.backend_agg"`). `grep -rn matplotlib src` → rỗng.
- **Chưa** thêm `matplotlib` vào `excludes` cho tới Phase 4 kiểm tra open3d có cần nó không.

**Commits:** `Replace matplotlib point-in-polygon with numpy`, `Draw report distribution chart with QPainter`,
`Remove matplotlib from runtime requirements`

---

## Phase 4 — Dọn bản build

### 4.1 Xác định open3d thực sự kéo theo gì
`tools/open3d_deps.py`: Python sạch, `import open3d`, in danh sách package cấp cao trong
`sys.modules` (so với trước khi import). Lưu `docs/dep-slimming/open3d-imports.txt`.
**Chỉ được exclude package không có trong danh sách này.** (Đã biết: `dash`, `plotly` có mặt
→ phải giữ.)

### 4.2 `build.spec`
- `hiddenimports`: xoá `"scipy"`, `"reportlab"`, `"matplotlib"`, `"matplotlib.backends.backend_agg"`,
  `"vtkmodules.all"`. Thay `collect_submodules("open3d")` bằng `["open3d", "open3d.cpu.pybind"]`
  + các submodule có trong `open3d-imports.txt` (bỏ `open3d.ml`, `open3d.visualization.gui`
  nếu không bị import).
- `datas`: thay `collect_data_files("open3d")` bằng danh sách cụ thể, **thử bỏ**
  `open3d/resources` (38 MB, tài nguyên GUI riêng của open3d), `nbextension`, `labextension`,
  `examples`. Kiểm chứng: exe chạy Calculate + Measure Area ra **đúng số golden**; nếu open3d báo
  thiếu resource → trả lại, ghi Nhật ký.
- `excludes`: `PyQt5`, `PyQt6`, `tkinter`, `scipy`, `reportlab`, `pytest`, `IPython`,
  `notebook`, `ipywidgets`, `matplotlib`, `jedi` — **trừ** những gì có trong
  `open3d-imports.txt`.
- `console=False` (log đã ghi ra file; `_install_excepthook` vẫn log). Nếu lỗi xảy ra trước khi
  có cửa sổ, hiện `QMessageBox.critical` trong excepthook **chỉ khi** đã có `QApplication`.
- Bảo đảm `upx=False` cho `EXE` và `COLLECT` (UPX làm antivirus nghi ngờ và chậm nạp).

### 4.3 VTK & pyvista
- Thêm cờ môi trường `PPS_DUMP_MODULES=<file>`: khi app thoát, ghi
  `sorted(m for m in sys.modules if m.startswith(("vtkmodules", "PySide6", "pyvista", "open3d")))`.
  (Trong `main.py`, sau `app.exec()`, chỉ khi biến tồn tại.)
- Chạy từ source, đi hết CHECKLIST.md (mọi tool, Calculate, xuất PDF, lưu/mở project, User
  Guide) → `docs/dep-slimming/used-modules.txt` (commit).
- `hook-vtkmodules.py`: thay `collect_submodules('vtkmodules')` bằng danh sách từ
  `used-modules.txt`.
- `hook-pyvista.py`: thay `collect_submodules('pyvista')` bằng import thực tế; exclude
  `pyvista.trame`, `pyvista.jupyter`, `pyvista.ext`.
- Sau build, liệt kê 20 file lớn nhất trong `_internal/vtk.libs`. Chỉ loại DLL **cụ thể** đã
  chứng minh không dùng (ví dụ `vtkIOParallel`, `vtkIOLSDyna`, `vtkIOExodus`, `vtkIOFFMPEG`,
  `vtkWebCore`, `vtkAcceleratorsVTKm*`) bằng cách lọc `a.binaries`; mỗi DLL bị loại phải qua
  CHECKLIST trên exe. Không dùng wildcard rộng.

### 4.4 Qt
- Giữ QtCore, QtGui, QtWidgets, QtSvg, QtOpenGL/QtOpenGLWidgets (pyvistaqt), các module có trong
  `used-modules.txt`. Exclude QtWebEngine*, Qt3D*, QtQuick*, QtQml*, QtMultimedia*, QtCharts,
  QtDataVisualization, QtPdf*, QtBluetooth, QtSerialPort, QtSql, QtTest (QtNetwork chỉ khi không
  có trong `used-modules.txt`). Bỏ `translations` Qt trừ `qtbase_en`.

### 4.5 Dọn mã chết
- `requirements.txt`: xoá `scipy`, `reportlab`, `matplotlib`; tách `pytest`, `pytest-qt`,
  `markdown` sang `requirements-dev.txt`; `matplotlib` vào `requirements-dev.txt` (chỉ cho test
  so khớp ở Phase 3).
- Xoá `src/pps/report/sections/` (chỉ còn `__pycache__`) và `__pycache__` cũ của
  `pdf_generator`, `style_factory`, `shotcrete_template`.

### 4.6 Kiểm chứng
Build, đi hết CHECKLIST.md trên exe. Thiếu module thường chỉ lộ ra khi dùng đúng chức năng đó.
Xuất PDF từ sample với cùng thông số như bản baseline → **mọi số liệu giống hệt**.

**Commits:** `Record open3d runtime imports`, `Trim unused packages and open3d data from the build`,
`Bundle only the VTK, pyvista and Qt modules in use`, `Remove dead report modules and dev deps from runtime requirements`

---

## Phase 5 — Venv sạch, build cuối, bàn giao

1. `python -m venv .venv-slim && .venv-slim\Scripts\pip install -r requirements.txt -r requirements-dev.txt`.
2. `pytest -q` trên `.venv-slim`.
3. Build bằng `.venv-slim\Scripts\pyinstaller build.spec --noconfirm`.
4. Đi hết CHECKLIST.md trên exe. So PDF với bản baseline (`baseline-pre-slim.zip`, cùng sample,
   cùng thông số): mọi số liệu giống hệt.
5. `tools/measure_startup.py`: warm (trung vị 3 lần). Chuẩn bị hướng dẫn để chủ dự án đo **cold
   sau khi khởi động lại máy** cho cả bản cũ và mới (mỗi lần khởi động lại chỉ đo 1 bản, vì
   bản chạy trước sẽ làm "ấm" các DLL dùng chung như Python/Qt nếu cùng đường dẫn — đo bản cũ
   và bản mới ở 2 lần khởi động lại khác nhau).
6. Cập nhật `installer.iss` nếu đường dẫn/tệp thay đổi; build installer, cài thử trên máy sạch.
7. Cập nhật `README.md` (yêu cầu cài đặt, kích thước) và ghi chú trong `docs/REFACTOR_PLAN.md`
   §0 (đã gỡ matplotlib/reportlab/scipy; open3d giữ, nạp ở nền).
8. Không xoá `.venv` cũ.
9. Báo cáo cuối: Nhật ký đo, danh sách commit/tag, rủi ro còn lại. **Không merge** — chủ dự án
   merge theo README §4.4.

**Commit:** `Finalize slim build: docs, installer and measurements`

---

## Nhật ký đo

| Phase | Ngày | dist MB | Số file | Module VTK lúc khởi động | Warm (s) | Cold sau reboot (s) | Calculate lần đầu / lần sau (s) | pytest | Ghi chú |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 2026-10-28 | 900 | 3277 | 153 | 3.29 (run 1: 14.65) | chờ đo | | 131 passed, 71 s | Import `main_window` từ source: 2.41 s warm (lần đầu trong `.venv` từng đo 288 s). Top importtime: `vtk` 704 ms, `pyvistaqt` 671 ms, `pyvista.plotting` 479 ms, `matplotlib.pyplot` 367 ms (do pyvista), `matplotlib.path` 236 ms (do `picking.py`) |
| 1 | | | | | | | | | |
| 2 | | | | | | | | | |
| 3 | | | | | | | | | |
| 4 | | | | | | | | | |
| 5 | | | | | | | | | |

---

## Phụ lục — Phương án dự phòng: bỏ open3d

**Không làm trong đợt này.** Chỉ cân nhắc nếu sau Phase 5 lần Calculate đầu hoặc dung lượng
vẫn không chấp nhận được, và chủ dự án đồng ý số diện tích/thể tích thay đổi.

- Thuật toán thay thế đã thử nghiệm: Delaunay 2D của VTK theo khối 1 m, R_MAX 0.07 m —
  lệch −1.0 % … +1.6 % so với open3d trên sample, ~4.4 s so với 12.4 s, không thêm gói.
- Bản tham chiếu: [reference_area.py](reference_area.py). Toàn bộ số liệu và các phương án đã
  loại (BPA numpy, port C++, đếm ô lưới …): [AREA_COMPARISON.md](AREA_COMPARISON.md).
- Nếu làm: cần kiểm chứng trên nhiều file PLY thật (±3 %), chủ dự án duyệt trước khi cập nhật
  golden; gỡ open3d sẽ bỏ thêm ~230 MB (open3d + dash + plotly + jedi).
