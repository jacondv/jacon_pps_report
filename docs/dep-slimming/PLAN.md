# Kế hoạch thực hiện theo phase

Đọc [README.md](README.md) (quy tắc + rollback) trước. Làm **tuần tự**. Mỗi phase kết thúc bằng:

```
.venv\Scripts\python -m pytest -q        # phải xanh
git commit ...                            # 1 hoặc vài commit nhỏ
git tag slim/phase-N-done
```

và ghi một dòng vào [Nhật ký đo](#nhật-ký-đo) ở cuối file.

---

## Phase 0 — Chuẩn bị & đo baseline

**Mục tiêu:** có điểm rollback và số đo để so sánh.

1. Xác nhận đang ở nhánh `perf/slim-deps`, working tree sạch, tag `baseline/pre-slim-deps` tồn tại.
2. `pip freeze > docs/dep-slimming/requirements-baseline.lock` → commit.
3. Nén `dist/Jacon PPS Report/` → `installer_output/baseline-pre-slim.zip` (không commit).
4. Tạo `tools/measure_startup.py` (script dev, không đóng gói):
   - Tham số: đường dẫn exe (hoặc `--source` để chạy `python main.py`), số lần chạy.
   - Ghi nhận thời điểm khởi chạy process → chờ dòng `MainWindow shown` xuất hiện trong
     `%LOCALAPPDATA%\TunnelAnalyzer\logs\app.log` (log đã có sẵn, xem `main.py`) → in số giây,
     rồi tắt process.
   - In thêm: tổng dung lượng và số file của thư mục chứa exe.
5. Đo baseline:
   - `python -X importtime main.py 2> docs/dep-slimming/importtime-baseline.txt` (đóng app ngay
     khi hiện cửa sổ). Ghi top 15 module import chậm nhất vào Nhật ký.
   - Build hiện tại: dung lượng, số file, thời gian khởi động warm (chạy 3 lần lấy trung vị).
   - Cold start: lần đầu thật sự chỉ đo đúng được trên máy/VM chưa từng chạy app. Nếu không có,
     ghi "chưa đo cold" — **không bịa số**.
6. Chạy `pytest -q`, ghi số test pass.

**Commit:** `Add dependency-slimming baseline lock and startup measurement script`

---

## Phase 1 — Gỡ gói không dùng (rủi ro thấp)

**Bằng chứng:** `grep -rn "scipy\|reportlab" src --include=*.py` → không có kết quả.

1. `requirements.txt`: xoá `scipy`, `reportlab`. Tách `pytest`, `pytest-qt`, `markdown` sang
   `requirements-dev.txt` mới (README chính cập nhật lệnh cài).
2. `build.spec`:
   - Xoá `"scipy"`, `"reportlab"` khỏi `hiddenimports`.
   - Thêm `excludes=["PyQt5", "PyQt6", "tkinter", "IPython", "jedi", "dash", "plotly",
     "notebook", "ipywidgets", "scipy", "reportlab", "pytest"]`.
   - Đổi `console=True` → `console=False` (log đã ghi ra file; `_install_excepthook` vẫn log
     exception). Kiểm tra lại: lỗi khởi động vẫn hiện được ra người dùng không — nếu
     `main()` lỗi trước khi có cửa sổ, thêm `QMessageBox.critical` trong excepthook **chỉ khi**
     đã có `QApplication`.
3. Xoá thư mục chết `src/pps/report/sections/` (chỉ còn `__pycache__`) và mọi `__pycache__`
   chứa `pdf_generator`, `style_factory`, `shotcrete_template` cũ trong `src/pps/report/`.
4. **Lưu ý:** open3d vẫn còn ở phase này nên dash/plotly có thể bị open3d import lúc chạy.
   Nếu exclude chúng làm `import open3d` lỗi trong bản build → tạm bỏ `dash`, `plotly` khỏi
   `excludes`, ghi chú lại, thêm lại ở Phase 4.
5. Build thử (`pyinstaller build.spec --noconfirm`), chạy exe, mở sample PLY, tính toán, xuất PDF.

**Commit:** `Drop unused scipy/reportlab and exclude stray packages from the build`

---

## Phase 2 — Bỏ matplotlib

### 2a. `render/picking.py` — `points_in_polygon`
- Thay `matplotlib.path.Path(polygon).contains_points(points)` bằng hàm numpy thuần
  (even-odd ray casting, vector hoá theo cạnh: lặp qua N cạnh của polygon, mỗi lần xử lý cả
  mảng điểm). Giữ nguyên chữ ký và nhánh `< 3 đỉnh / 0 điểm → all False`.
- Polygon lasso có thể có hàng trăm đỉnh, số điểm cloud có thể hàng triệu → kiểm tra hiệu năng:
  lọc trước bằng bounding box của polygon, chỉ chạy ray casting trên điểm trong bbox.
- **Test mới** `tests/test_picking.py`:
  - So khớp với matplotlib trên 100k điểm ngẫu nhiên × (hình chữ nhật, polygon lõm, lasso 300
    đỉnh tự cắt nhẹ). Dùng `pytest.importorskip("matplotlib")` để test chạy được trên máy dev
    có matplotlib, và bị skip trên venv slim. Cho phép lệch **chỉ** với điểm nằm cách cạnh
    < 1e-9 px.
  - Ca biên: polygon suy biến, điểm rỗng.
  - Benchmark: 2 triệu điểm × lasso 300 đỉnh không chậm hơn matplotlib quá 2 lần.

### 2b. Biểu đồ phân bố trong PDF — `report/core/html_pdf_generator.py::_create_distribution_chart`
- Vẽ lại bằng **QPainter → QImage → PNG** (PySide6 có sẵn), giữ nguyên:
  - Kích thước tương đương `figsize=(8, 4.5)` @ `dpi=150` → 1200×675 px.
  - 3 cột, nhãn `< {tmin}`, `{tmin}-{tmax}`, `> {tmax}`; màu `#ff6060`, `#64ffa0`, `#315aff`.
  - Nhãn trên đỉnh cột `"{count:,}\n({percent:.0f}%)"`, tiêu đề "Thickness Distribution" đậm,
    trục X "Thickness Range (mm)", trục Y "Number of Points", lưới ngang nét đứt mờ,
    khoảng trống trên 20 % (`margins(y=0.2)`), các vạch số trục Y dạng "nice numbers".
  - Vẫn ghi ra file tạm `pps_report_distribution_*.png` và trả về đường dẫn → **key
    `chart_path` và template HTML không đổi**.
  - Cột 0 điểm không vẽ (chiều cao 0) nhưng vẫn có nhãn `0 (0%)`.
- Đặt code vẽ ở module riêng `src/pps/report/charts.py` (không phụ thuộc UI). QPainter trên
  QImage cần `QGuiApplication` tồn tại — trong app luôn có; trong test dùng fixture `qapp`.
- Font: dùng font mặc định của app; đảm bảo chữ đọc được ở 1200 px rộng (tiêu đề ~32 px,
  nhãn ~24 px).
- **Test:** tạo PNG, kiểm tra kích thước, file hợp lệ; xuất 1 PDF mẫu và **lưu ảnh chart cũ
  vs mới** vào `docs/dep-slimming/compare/` để chủ dự án so bằng mắt.

### 2c. Gỡ
- Xoá `matplotlib` khỏi `requirements.txt`, `hiddenimports` (`"matplotlib"`,
  `"matplotlib.backends.backend_agg"`), thêm `"matplotlib"` vào `excludes`.
- Kiểm tra pyvista không import matplotlib trong luồng dùng thực tế (code không truyền
  `cmap` dạng chuỗi — đã kiểm tra: không có `cmap` nào trong `src/`).
- `grep -rn matplotlib src` → rỗng.

**Commits:** `Replace matplotlib point-in-polygon with numpy`,
`Draw report distribution chart with QPainter`, `Remove matplotlib dependency`

---

## Phase 3 — Bỏ open3d (thay thuật toán diện tích) ⚠️ cần duyệt

### 3.1 Hiện trạng cần thay
`core/surface_area.py::surface_area(pcd, radii)` dùng open3d:
1. `voxel_down_sample(voxel_size=min(radii)/2)` — trung bình toạ độ các điểm trong mỗi voxel.
2. `remove_radius_outlier(nb_points=8, radius=2*min(radii))`.
3. Ước tính normal (`KDTreeSearchParamHybrid(radius=2*max(radii), max_nn=30)`) + định hướng.
4. Ball Pivoting → mesh → `get_surface_area()`.

Được gọi với `radii=(0.05, 0.1)` từ:
- `core/calculator.py::calculate_area_and_volume` — tổng diện tích **và** diện tích đạt chiều
  dày (`area_reached_target_m2`, chỉ khi ≥ 100 điểm); thể tích = diện tích đạt × chiều dày TB.
- `core/analysis.py::compute_area_m2` — tool Measure Area (vùng chọn nhỏ).

### 3.2 Phương án đã chốt (2026-10-28): Delaunay 2D của VTK theo khối 1 m

Đã thử và loại (chi tiết ở [AREA_COMPARISON.md](AREA_COMPARISON.md)):
- BPA viết lại bằng Python+numpy: 67 s (chậm ~5×), chia khối + multiprocessing vẫn 20–37 s.
- Port BPA sang C++: cần MSVC — **loại vì công ty không có license Visual Studio**. Yêu cầu:
  toàn bộ toolchain và thư viện phải miễn phí cho dùng thương mại/nội bộ.
- Đếm ô lưới chiếu: lệch −35 % … −2 %. Delaunay trên 1 mặt phẳng chung: −53 % (vòm hầm gập).
- Delaunay có hiệu chỉnh normal: −8 % trên dữ liệu thật.

Thuật toán chốt (bản tham chiếu đã chạy thử: [reference_area.py](reference_area.py)):
1. **Giảm mẫu voxel** cạnh `min(radii)/2` = 0.025 m, lấy trọng tâm mỗi voxel (numpy).
2. **Lọc nhiễu**: giữ điểm có ≥ 8 láng giềng (tính cả chính nó) trong bán kính `2*min(radii)`
   = 0.1 m. Láng giềng tìm bằng băm lưới cell = bán kính, xét 27 cell lân cận (numpy).
3. **Chia khối 1×1×1 m**, mỗi khối mở rộng thêm lề 0.25 m.
4. Mỗi khối: PCA → mặt phẳng khớp nhất → chiếu điểm thành (u, v) →
   `pyvista.PolyData(...).delaunay_2d()` chỉ để lấy cách nối tam giác.
5. Với từng tam giác, dùng **toạ độ 3D gốc**: bỏ tam giác có bán kính đường tròn ngoại tiếp 3D
   > `R_MAX = 0.07` m hoặc suy biến; chỉ giữ tam giác có **trọng tâm nằm trong lõi khối**
   (không tính lề) → không mất/không trùng tam giác ở biên khối.
6. Diện tích = tổng diện tích 3D các tam giác giữ lại.

Hằng số (`BLOCK_SIZE_M = 1.0`, `BLOCK_MARGIN_M = 0.25`, `R_MAX_M = 0.07`) đặt ở đầu
`core/surface_area.py`, có docstring giải thích lý do chọn và tham chiếu tới AREA_COMPARISON.md.

Chữ ký mới: `surface_area(points: np.ndarray, radii=(0.05, 0.1)) -> float` — nhận numpy
array, không còn kiểu PointCloud. Xoá `_to_open3d_pointcloud`, sửa các chỗ gọi.
Chỉ dùng numpy + pyvista/VTK (đã có sẵn) — **không thêm gói nào, không dùng scipy**.

### 3.3 Kiểm chứng trước khi áp dụng
`tools/compare_area.py` (dev-only; cần open3d → `requirements-compare.txt`, ghi chú "chỉ để so
sánh, không dùng lúc chạy"). Giữ bản open3d cũ trong script này làm tham chiếu. Script chạy
trên **mọi file `.ply` trong một thư mục truyền vào** (chủ dự án sẽ cung cấp thêm file thật:
hầm thẳng, đoạn cong, vách/góc) và in bảng: toàn bộ cloud + tập đạt target > 20/40/50/100 mm
(sau khi clip |d|<12 và |d|>500 như `calculate_area_and_volume`) + 5 vùng con 1–5 m².

Kết quả đã đo trên sample (đích cần tái lập, R = 0.07, khối 1 m):

| Tập điểm | open3d BPA | Delaunay VTK | Lệch |
|---|---|---|---|
| Toàn bộ cloud | 99.748 | 98.727 | −1.0 % |
| Đạt target > 20 mm | 16.588 | 16.771 | +1.1 % |
| > 40 mm (golden case 0) | 14.154 | 14.344 | +1.3 % |
| > 50 mm (golden case 1) | 13.775 | 13.925 | +1.1 % |
| > 100 mm | 11.727 | 11.918 | +1.6 % |
| Thời gian toàn bộ cloud | 11.5 s | ~4.5 s (gồm tiền xử lý) | |

**Tiêu chí chấp nhận:** trên mọi file được cung cấp, lệch so với open3d ≤ ±3 % cho toàn bộ
cloud và các tập đạt target; nhanh hơn open3d. File nào vượt ngưỡng → ghi lại, **không tự
chỉnh `R_MAX`/kích thước khối để khớp** — báo cáo cho chủ dự án.

### 3.4 Điểm dừng — chờ chủ dự án duyệt
Ghi bảng kết quả trên các file thật vào `AREA_COMPARISON.md` (mục "Kiểm chứng trên dữ liệu
thật"). **Dừng lại, báo cáo, chờ duyệt.** Chưa sửa golden, chưa gỡ open3d.

### 3.5 Sau khi được duyệt
1. Áp dụng thuật toán 3.2 vào `core/surface_area.py`; cập nhật `calculator.py`,
   `analysis.py` (bỏ `import open3d`). Giữ nguyên: ngưỡng 100 điểm, công thức thể tích,
   in-place mutation của `distances`, `AREA_MEASUREMENT_RADII`.
2. Golden: viết `tests/golden/update_area_fields.py` chỉ cập nhật 3 trường `surface_area_m2`,
   `volume_m3`, `area_reached_target_m2` trong `sample_baseline.json`; mọi trường khác phải
   giữ nguyên (script tự assert điều này). Ghi chú lý do + ngày + người duyệt ở đầu
   `test_calculator_golden.py`.
3. Test mới `tests/test_surface_area.py`: nửa trụ R = 3 m dài 2 m (đúng 18.850 m², nhiễu
   σ = 3 mm, chấp nhận ±3 %); mặt phẳng 2×3 m có lỗ tròn R = 0.5 m (đúng 5.215 m², ±6 % — đo được +5.1 % — Delaunay
   đếm cả độ gồ ghề của nhiễu); cloud rỗng → 0; cloud toàn outlier → 0; một khối duy nhất;
   cloud trải qua nhiều khối cho cùng kết quả khi dịch gốc toạ độ ±0.3 m (±1 %); deterministic.
4. Xoá `open3d` khỏi `requirements.txt`, `build.spec` (`collect_data_files("open3d")`,
   `collect_submodules("open3d")`, `"open3d"` trong `hiddenimports`); thêm `"open3d"` vào
   `excludes`. Nếu Phase 1 đã tạm bỏ `dash`/`plotly` khỏi `excludes`, thêm lại.
5. `grep -rn open3d src build.spec requirements.txt` → rỗng.

**Commits:** `Add area comparison script`, `Replace open3d BPA surface area with block-wise VTK Delaunay`,
`Update golden area fields after approved algorithm change`, `Remove open3d dependency`

---

## Phase 4 — Import trễ (lazy import) để cửa sổ hiện nhanh hơn

Dựa trên `importtime-baseline.txt`, dời import nặng không cần cho lúc mở cửa sổ:
1. `ui/main_window.py:31` `from pps.report import PDFGenerator` → import bên trong handler xuất
   PDF (quanh dòng 796). Kéo theo jinja2, pdfkit không còn nạp lúc khởi động.
2. `app/workers.py` / `core/analysis.py`: import module tính toán trong `run()` của worker nếu
   importtime cho thấy đáng kể.
3. Không làm lazy những gì cửa sổ cần ngay (PySide6, pyvistaqt, vtk viewport).
4. Thêm splash screen (`QSplashScreen` với `assets/` logo) hiện **trước** khi import
   `pps.ui.main_window` trong `main.py`, đóng sau `window.showMaximized()`. Người dùng thấy
   phản hồi ngay cả khi Defender đang quét.
5. Đo lại `-X importtime` → `importtime-after.txt`, ghi so sánh vào Nhật ký.
6. Đảm bảo `tests/test_main_window_smoke.py` và test xuất report vẫn xanh (monkeypatch có thể
   phải trỏ tới đường dẫn import mới).

**Commit:** `Defer report imports and show a splash screen during startup`

---

## Phase 5 — Lọc VTK và Qt trong bản build

### 5a. Tìm module thực sự dùng
- Thêm cờ môi trường `PPS_DUMP_MODULES=<file>`: khi app thoát, ghi
  `sorted(m for m in sys.modules if m.startswith(("vtkmodules", "PySide6", "pyvista")))` ra
  file. (Đặt trong `main.py`, sau `app.exec()`, chỉ khi biến tồn tại.)
- Chạy từ source, đi hết [CHECKLIST.md](CHECKLIST.md) (mọi tool, xuất PDF, mở/lưu project,
  User Guide), rồi thoát → được danh sách module.
- Lưu danh sách vào `docs/dep-slimming/used-modules.txt` (commit).

### 5b. Cấu hình build
- `hook-vtkmodules.py`: thay `collect_submodules('vtkmodules')` bằng danh sách từ 5a + các
  module VTK nạp động mà pyvista cần (`vtkRenderingOpenGL2`, `vtkInteractionStyle`,
  `vtkRenderingFreeType`, `vtkRenderingContextOpenGL2`, `vtkRenderingUI` …).
  Xoá `"vtkmodules.all"` khỏi `hiddenimports` trong `build.spec`.
- `hook-pyvista.py`: thay `collect_submodules('pyvista')` bằng import thực tế; exclude
  `pyvista.trame`, `pyvista.jupyter`, `pyvista.ext`.
- Qt: chỉ giữ QtCore, QtGui, QtWidgets, QtSvg, QtOpenGL/QtOpenGLWidgets (pyvistaqt cần),
  QtPrintSupport (nếu 5a thấy có). Exclude QtWebEngine*, Qt3D*, QtQuick*, QtQml*,
  QtMultimedia*, QtCharts, QtDataVisualization, QtPdf*, QtNetwork (nếu không dùng),
  QtBluetooth, QtSerialPort, QtSql, QtTest. Xoá thư mục `translations` Qt không cần
  (chỉ giữ `qtbase_en`).
- Sau build, kiểm tra trong `_internal/vtk.libs` và `_internal/PySide6`: liệt kê 20 file lớn
  nhất, ghi vào Nhật ký. Nếu `vtk.libs` vẫn chứa DLL lớn rõ ràng không dùng (ví dụ
  `vtkIOParallel`, `vtkFiltersParallel*`, `vtkRenderingVolume*`, `vtkIOExodus`, `vtkIOFFMPEG`,
  `vtkWrapping*` …) thì lọc bằng cách sửa `a.binaries` trong `build.spec` theo danh sách
  loại trừ **cụ thể** — từng DLL bị loại phải được kiểm chứng bằng CHECKLIST trên exe.
  Không dùng wildcard rộng.

### 5c. Kiểm chứng
- Chạy exe đã build, đi hết CHECKLIST.md. Thiếu module → lỗi thường chỉ hiện khi dùng tới
  chức năng đó, nên **không được bỏ mục nào**.
- Nếu một DLL loại trừ gây lỗi → trả lại DLL đó, ghi vào Nhật ký.

**Commits:** `Add module-usage dump for build trimming`, `Trim VTK, pyvista and Qt modules from the build`

---

## Phase 6 — Venv sạch, build cuối, bàn giao

1. Tạo venv sạch: `python -m venv .venv-slim && .venv-slim\Scripts\pip install -r requirements.txt -r requirements-dev.txt`
   (`requirements-dev.txt` lúc này **không** có open3d/matplotlib — chuyển chúng sang
   `requirements-compare.txt` riêng cho các script so sánh).
2. `pytest -q` trên `.venv-slim` (các test so sánh với matplotlib/open3d sẽ skip — đúng ý).
3. Build bằng `.venv-slim`: `.venv-slim\Scripts\pyinstaller build.spec --noconfirm`.
4. Đi hết CHECKLIST.md trên exe. Xuất PDF từ sample, so với PDF baseline (giải nén từ
   `baseline-pre-slim.zip`, xuất cùng sample + cùng thông số): mọi số liệu giống hệt, trừ
   diện tích/thể tích đã duyệt ở Phase 3.
5. Đo bằng `tools/measure_startup.py`; nếu có máy/VM sạch, đo cold start cả bản cũ lẫn mới.
6. Cập nhật `installer.iss` nếu có đường dẫn/tệp thay đổi; build installer, thử cài trên máy sạch.
7. Cập nhật `README.md` (yêu cầu cài đặt, kích thước), `docs/REFACTOR_PLAN.md` §0 dòng "Giữ thư
   viện chính" (ghi chú đã gỡ open3d/matplotlib/reportlab/scipy).
8. Không xoá `.venv` cũ — để chủ dự án quyết định.
9. Báo cáo cuối: bảng Nhật ký đo, danh sách commit/tag, các rủi ro còn lại. **Không merge**;
   chủ dự án merge theo README §4.4.

**Commit:** `Finalize slim build: docs, installer and measurements`

---

## Nhật ký đo

| Phase | Ngày | dist MB | Số file | Khởi động warm (s, trung vị 3 lần) | Cold (s) | pytest | Ghi chú |
|---|---|---|---|---|---|---|---|
| baseline | 2026-10-28 | 907 | 3276 | | | | Số MB/file đo lúc lập kế hoạch |
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |
| 6 | | | | | | | |
