# Checklist kiểm thử thủ công

Chạy **trên exe đã build** (không chỉ từ source) ở cuối Phase 1, 2, 3, 5, 6. Thiếu module trong
bản build thường chỉ lộ ra khi dùng tới đúng chức năng đó — không bỏ mục nào.
Dữ liệu: `sample/2_thickness_01#20260203_093652#cloud_compared_07.ply`.

Ghi kết quả: copy bảng cuối file vào Nhật ký của phase, đánh ✅ / ❌ + ghi chú.

## Khởi động
- [ ] Double-click exe → splash (từ Phase 4) → cửa sổ maximized, không có cửa sổ console (từ Phase 1).
- [ ] `%LOCALAPPDATA%\TunnelAnalyzer\logs\app.log` có đủ các dòng khởi động, không có ERROR.
- [ ] Đổi theme sáng/tối trong Settings, khởi động lại → giữ theme.

## Mở dữ liệu & hiển thị
- [ ] Mở sample PLY → chọn field `distances` → cloud hiện, có màu theo chiều dày, color legend đúng.
- [ ] Thông tin từ tên file (filename parser) hiện đúng trong Project dock.
- [ ] Xoay / zoom / pan; các nút camera (trước/sau/trên/…; reset view).
- [ ] Layer: tạo layer theo khoảng chiều dày, ẩn/hiện, đổi màu, xoá.

## Tool tương tác
- [ ] Region select: rectangle, polygon, lasso — số điểm chọn hợp lý; thêm/bớt vùng chọn.
- [ ] Tạo segment/layer từ vùng chọn.
- [ ] Measure Distance: chọn 2 điểm, nhãn bám theo khi xoay.
- [ ] Measure Area: chọn vùng → ra diện tích (m²) không lỗi, spinner hiện khi đang tính.
- [ ] Note / Annotation: tạo, sửa inline, xoá; nhãn bám điểm 3D.
- [ ] Undo/Redo (Ctrl+Z / Ctrl+Y) cho từng thao tác trên.

## Tính toán
- [ ] Chạy Calculate → Results dock có diện tích, thể tích, mean/min/max/std, phân bố Below/Within/Above.
- [ ] So với baseline (cùng target min/max): mọi số giống hệt, trừ diện tích/thể tích sau Phase 3 (đã duyệt).

## Project file
- [ ] Lưu `.ppsproj` → đóng → mở lại: layer, ghi chú, số đo, camera khôi phục đúng.

## Xuất báo cáo
- [ ] Xuất PDF: mở được, có ảnh chụp viewer (có số đo/ghi chú), biểu đồ phân bố, bảng số liệu, ghi chú segment.
- [ ] Biểu đồ (từ Phase 2): màu, nhãn, tiêu đề, trục đúng như bản cũ.

## Trợ giúp
- [ ] Help → User Guide (HTML) mở được.
- [ ] Help → User Guide PDF mở được.
- [ ] About dialog hiện đúng phiên bản.

## Bảng ghi kết quả

| Mục | Phase 1 | Phase 2 | Phase 3 | Phase 5 | Phase 6 |
|---|---|---|---|---|---|
| Khởi động | | | | | |
| Mở dữ liệu & hiển thị | | | | | |
| Tool tương tác | | | | | |
| Tính toán | | | | | |
| Project file | | | | | |
| Xuất báo cáo | | | | | |
| Trợ giúp | | | | | |
