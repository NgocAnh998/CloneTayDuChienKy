# Báo cáo phân tích Tây Du Chiến Ký (TDCK-HBTG-320x240.jar)

> Phạm vi: chỉ phân tích từ JAR mà người dùng cung cấp. Các kết luận dưới đây được đối chiếu với bytecode và/hoặc được kiểm tra bằng parser chạy trên toàn bộ tài nguyên tương ứng.

## 1. Tổng quan

- MIDlet: `Tay Du Chien Ky`; entry class: `lx.game.XMidlet`.
- Java ME, CLDC 1.0 / MIDP 1.0.
- 1.331 entry ZIP/JAR (1.319 file); tổng dữ liệu giải nén khoảng 2.261.635 byte.
- 820 `.ms`, 157 `.png`, 124 `.map`, 123 `.act`, 78 `.class`, 10 `.dat`, 4 `.bin`.

## 2. Script .ms — XOR đã xác minh

Trong `lx.game.af.e(String)`, game đọc resource, kiểm tra phần mở rộng `.ms` rồi XOR từng byte với `0x01`. Phép biến đổi này được áp dụng cho 820/820 file. Nội dung sau XOR vẫn có header nhị phân và ngôn ngữ lệnh/chuỗi; giải XOR không đồng nghĩa đã có interpreter ngữ nghĩa.

## 3. Map — parser kiểm thử 124/124

Định dạng big-endian theo DataInputStream:
1. Hai short đầu.
2. UTF tên tileset.
3. short rows, short columns.
4. Hai byte tile width/height.
5. Hai ma trận byte kích thước rows × columns.
6. short staticCount; mỗi entry có hai UTF.
7. short objectCount; mỗi entry có short x, short y, UTF descriptor.

Parser đọc hết dữ liệu, không dư byte và không lỗi với 124/124 map. Tile index dùng abs(value)-1; 0 là bỏ qua. Transform 2 được xác định là lật ngang trong nhánh Nokia DirectGraphics.

Ví dụ: map 1 dùng map3.png, lưới 10 × 37, tile 32 × 32, kích thước thế giới 1.184 × 320 pixel và 30 object descriptors.

## 4. ACT — LXA2 và legacy

Class `lx.game.ar` đọc ACT. Định dạng mới có magic `LXA2`, metadata atlas, rectangles crop, animation groups, frames và sequences. Trong 123 ACT: 106 LXA2, 17 legacy; parser đọc trọn 110/123, còn 13 file legacy có byte cuối chưa giải nghĩa. Dữ liệu dư được giữ lại trong index, không bị bỏ.

`sunwk.act` tham chiếu `sunwk.png` và `sunwk1.png`, có 96 rectangle, 154 animation group và 50 sequence.

## 5. Class quan trọng

- `lx.game.XMidlet`: điểm vào MIDlet.
- `lx.game.af`: điều phối/tài nguyên; đọc MS, parse map, helper vẽ ảnh.
- `lx.game.ar`: đọc ACT.
- `lx.game.e`: render tilemap.
- `lx.game.m`: sprite logic kế thừa từ ar.

## 6. Runtime prototype

Prototype Canvas 320 × 240:
- Chọn trong 124 map, render tiles và transform, camera cuộn.
- Ghép Tôn Ngộ Không từ atlas bằng rectangle/frame metadata trong sunwk.act.
- Dùng sequence animation thử nghiệm và hiển thị object markers.

Input, tốc độ, biên và camera chỉ là runtime thử nghiệm; chưa xác minh trùng gameplay Java ME. Chưa có collision, AI, combat, skill, quest hoặc script interpreter.

## 7. Việc tiếp theo

1. Phân tích 10 file .dat.
2. Xây parser semantic/interpreter cho .ms.
3. Giải nghĩa 13 ACT legacy còn byte dư.
4. Reverse-engineer collision, movement, AI, damage, loot, quest và save.
5. Chuyển runtime sang JavaScript/Phaser sau khi hiểu dữ liệu và logic gốc.

**Kết luận:** đây là nền tảng reverse-engineering đã kiểm chứng một phần, chưa phải game clone hoàn chỉnh.
