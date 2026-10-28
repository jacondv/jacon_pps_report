# Checklist kiểm thử thủ công

Chạy **trên exe đã build** (không chỉ từ source) ở cuối Phase 1, 2, 3, 4, 5. Thiếu module trong
bản build thường chỉ lộ ra khi dùng tới đúng chức năng đó — không bỏ mục nào.
Dữ liệu: `sample/2_thickness_01#20260203_093652#cloud_compared_07.ply`.

Ghi kết quả vào bảng cuối file, đánh ✅ / ❌ + ghi chú.

## Khởi động
- [ ] Double-click exe → splash hiện ngay (từ Phase 2) → cửa sổ maximized; không có cửa sổ
      console (từ Phase 4).
- [ ] `%LOCALAPPDATA%\TunnelAnalyzer\logs\app.log` có đủ các dòng khởi động, không có ERROR;
      có dòng `open3d preloaded in …` (từ Phase 2).
- [ ] Đóng app ngay khi vừa hiện cửa sổ (preload open3d chưa xong) → app thoát sạch, không treo.
- [ ] Đổi theme sáng/tối trong Settings, khởi động lại → giữ theme.

## Mở dữ liệu & hiển thị
- [ ] Mở sample PLY → chọn field `distances` → cloud hiện, màu theo chiều dày, color legend có chữ đúng font.
- [ ] Thông tin từ tên file hiện đúng trong Project dock.
- [ ] Xoay / zoom / pan mượt; các nút camera (trước/sau/trên…, reset view).
- [ ] Layer: tạo theo khoảng chiều dày, ẩn/hiện, đổi màu, xoá.

## Tool tương tác
- [ ] Region select: rectangle, polygon, lasso — số điểm chọn hợp lý; thêm/bớt vùng chọn.
- [ ] Tạo segment/layer từ vùng chọn.
- [ ] Measure Distance: chọn 2 điểm (picking), nhãn bám theo khi xoay.
- [ ] Measure Area: chọn vùng → ra diện tích (m²) không lỗi, spinner hiện khi đang tính.
- [ ] Note / Annotation: tạo, sửa inline, xoá; nhãn 3D (billboard) bám điểm.
- [ ] Undo/Redo (Ctrl+Z / Ctrl+Y) cho từng thao tác trên.

## Tính toán
- [ ] Calculate lần đầu (sau khi log preload xong) → Results dock có diện tích, thể tích,
      mean/min/max/std, phân bố Below/Within/Above. Ghi thời gian lần đầu và lần 2.
- [ ] Số liệu **giống hệt** baseline với cùng target min/max (case golden: 40/60 → diện tích
      99.748 m², đạt target 14.154 m², thể tích 2.968 m³).

## Project file
- [ ] Lưu `.ppsproj` → đóng → mở lại: layer, ghi chú, số đo, camera khôi phục đúng.

## Xuất báo cáo
- [ ] Xuất PDF: mở được, có ảnh chụp viewer (có số đo/ghi chú), biểu đồ phân bố, bảng số liệu,
      ghi chú segment.
- [ ] Biểu đồ (từ Phase 3): màu, nhãn, tiêu đề, trục như bản cũ.

## Trợ giúp
- [ ] Help → User Guide (HTML) mở được.
- [ ] Help → User Guide PDF mở được.
- [ ] About dialog hiện đúng phiên bản.

## Bảng ghi kết quả

| Mục | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---|---|---|---|---|
| Khởi động | | | | | |
| Mở dữ liệu & hiển thị | | | | | |
| Tool tương tác | | | | | |
| Tính toán | | | | | |
| Project file | | | | | |
| Xuất báo cáo | | | | | |
| Trợ giúp | | | | | |
