# Tây Du Chiến Ký — Reverse Engineering Foundation

Gói nền tảng phân tích từ duy nhất `TDCK-HBTG-320x240.jar` mà người dùng cung cấp.

## Chạy bản runtime dùng asset thật

Mở trực tiếp `game-prototype.html` bằng Chrome hoặc Edge. Bản thử nghiệm hiện có bản đồ cuộn, chọn được 124 map và 126 cảnh có map tương ứng từ script `.ms`, tự đặt nhân vật tại tọa độ xuất hiện được khai báo trong script, hiển thị object marker và điều khiển Tôn Ngộ Không bằng WASD/phím mũi tên. Cảnh map, tileset, sprite atlases, crop rectangles và các frame đều lấy từ JAR.

Điều khiển di chuyển đang là bước dựng runtime ban đầu, chưa được xác minh là chuyển động gốc của game. Bản này chưa có va chạm, quái, combat, nhiệm vụ hay interpreter script.

## Công cụ xem dữ liệu

- Mở `viewer/index.html` để xem 124 bản đồ cùng object descriptors.
- Mở `viewer/sprites.html` để xem các nhóm ACT, sequence và các phần sprite được ghép từ atlas.

Cả hai file đều tự nhúng dữ liệu và ảnh, không cần Internet, Node.js hoặc server. Trong `game-prototype.html`, chọn **Cảnh gốc** để tải tên cảnh, map và tọa độ xuất hiện lấy từ script `.ms`; dropdown **Map** vẫn cho phép kiểm tra map riêng.

## Nội dung chính

- `build/raw/`: toàn bộ cây tài nguyên trích từ JAR, bao gồm `.class` và resource nguyên gốc.
- `build/assets/script/decoded/`: 820 file `.ms` sau XOR `0x01`, giữ cấu trúc thư mục.
- `build/assets/map/`: map và tileset.
- `build/assets/sprite/`: `.act` và ảnh sprite.
- `build/assets/data/`: 10 file `.dat`.
- `build/assets/ui/`: ảnh UI, logo và icon gốc.
- `build/analysis/map-index.json`: cấu trúc đã parse của 124 map.
- `build/analysis/act-index.json`: cấu trúc đã parse của 123 ACT; byte legacy chưa đọc được vẫn được lưu lại.
- `analysis/REVERSE_ENGINEERING_REPORT.md`: báo cáo chi tiết và các giới hạn hiện tại.
- `analysis/bytecode/`: kết quả `javap` để tra cứu bytecode.
- `tools/`: scripts tái tạo dữ liệu và preview.

## Chạy lại bộ trích xuất

Cần Python 3.10+:

```bash
python tools/tdck_unpack.py TDCK-HBTG-320x240.jar --out build
python tools/build_viewer.py
python tools/build_sprite_viewer.py
python tools/build_game_prototype.py
python tools/verify_build.py
python tools/render_map_preview.py 101 --out previews/map-101.png --scale 1
```

Khi chạy lại bộ trích xuất, đặt JAR ở đường dẫn phù hợp hoặc truyền đường dẫn tuyệt đối. `tdck_unpack.py` tự sinh `ms-index.json`. Khi chỉ muốn lập chỉ mục lại script mà không trích xuất toàn bộ JAR, chạy `python tools/parse_ms.py build/assets/script/decoded --out build/analysis/ms-index.json`. Thêm `--include-commands` để lưu mọi token thô (tệp JSON sẽ lớn hơn). Script dùng thư viện chuẩn Python; script render preview cần Pillow.

## Trạng thái trung thực

Đây là bộ nền tảng reverse-engineering, **không phải game clone hoàn chỉnh**. Parser map đã qua kiểm tra 124/124; 110/123 ACT được đọc trọn vẹn; `.ms` đã được XOR đúng như bytecode gốc; 820 file đều đọc được payload UTF-8 sau header sáu byte, nhưng header và interpreter semantic vẫn chưa được giải nghĩa đầy đủ. Chỉ ba opcode trường cảnh lặp lại đã được dùng để lấy tên/map/tọa độ. 10 file `.dat` chưa được giải mã cấu trúc. Xem báo cáo trong `analysis/REVERSE_ENGINEERING_REPORT.md`.
