# Tây Du Chiến Ký – JavaScript Edition

Bản dựng lại game 2D chạy offline trên trình duyệt, ưu tiên khôi phục gameplay gốc trước khi mở rộng.

## Trạng thái

Đây là nền móng kỹ thuật và prototype chơi thử. Chưa phải bản clone hoàn chỉnh: cần JAR gốc để trích xuất map, sprite, animation, dữ liệu nhiệm vụ và phân tích logic Java ME.

## Chạy game

Mở trực tiếp `index.html` bằng Chrome/Edge. Không cần server, tài khoản hoặc kết nối Internet.

## Điều khiển prototype

- WASD / phím mũi tên: di chuyển
- J: đánh thường
- K: kỹ năng
- E: tương tác
- Shift: lướt

## Cấu trúc

- `index.html`: màn hình game
- `style.css`: giao diện
- `src/game.js`: vòng lặp Canvas, bản đồ, nhân vật, quái, chiến đấu và HUD

## Kế hoạch khôi phục bản gốc

1. Trích xuất và lập chỉ mục tài nguyên từ `TayDuChienKy-HBTG.jar`.
2. Phân tích `.map`, `.act`, `.ms` và bytecode `.class`.
3. Thay sprite/map prototype bằng tài nguyên gốc.
4. Khôi phục công thức chiến đấu, nhiệm vụ, NPC, trang bị và tiến trình.
5. Đối chiếu từng màn chơi với bản Java ME.

## Nguyên tắc

Không tuyên bố tính năng nào đã được khôi phục nếu chưa có dữ liệu hoặc kiểm chứng từ game gốc.