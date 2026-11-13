# Báo cáo phân tích Tây Du Chiến Ký (TDCK-HBTG-320x240.jar)

> Phạm vi: chỉ phân tích từ JAR mà người dùng cung cấp. Các kết luận dưới đây được đối chiếu với bytecode và/hoặc được kiểm tra bằng parser chạy trên toàn bộ tài nguyên tương ứng.

## 1. Tổng quan gói JAR

- MIDlet: `Tay Du Chien Ky`
- Lớp khởi chạy: `lx.game.XMidlet`
- Nền tảng: Java ME, CLDC 1.0 / MIDP 1.0
- 1.331 entry trong ZIP/JAR (gồm cả thư mục); 1.319 file; tổng dữ liệu file giải nén khoảng 2.261.635 byte.

| Phần mở rộng | Số lượng | Vai trò đã nhận diện |
|---|---:|---|
| `.ms` | 820 | Script/kịch bản/nội dung game; từng byte được XOR `0x01` trước khi game đọc |
| `.png` | 157 | Tileset, sprite atlas, ảnh giao diện |
| `.map` | 124 | Bản đồ và dữ liệu đối tượng |
| `.act` | 123 | Sprite atlas rectangles và animation metadata |
| `.class` | 78 | Java bytecode |
| `.dat` | 10 | Các bảng dữ liệu game (`mission`, `skill`, `goods`, `exp`, ...) |
| `.bin` | 4 | Dữ liệu nhị phân phụ trợ |
| Khác | 3 | `.txt`, `.mf`, `.mid` |

## 2. Định dạng `.ms` — ĐÃ XÁC MINH XOR

Trong `lx.game.af.e(String)`, game đọc resource, kiểm tra phần mở rộng `.ms` rồi XOR từng byte với số `1` (`ixor 1`). Công cụ `tools/tdck_unpack.py` áp dụng đúng phép biến đổi này cho toàn bộ **820 file**, giữ nguyên cấu trúc thư mục trong `build/assets/script/decoded/`.

Các file sau bước XOR vẫn chứa header nhị phân ở đầu và một ngôn ngữ script dạng lệnh/chuỗi phân tách bằng `|`. Vì vậy, “đã giải mã XOR” không có nghĩa là đã hoàn tất giải mã ngữ nghĩa hay viết xong interpreter. Bước tiếp theo là nhận diện header, opcode và luồng chạy của script.

## 3. Script `.ms` — ĐÃ LẬP CHỈ MỤC, CHƯA GIẢI NGHĨA INTERPRETER

Tất cả **820/820** file `.ms` được giải mã XOR `0x01` và phần payload sau sáu byte đầu đọc được bằng UTF-8 nghiêm ngặt. Payload dùng chuỗi lệnh phân tách bằng ký tự `|`; nhiều lệnh bắt đầu bằng ba chữ số. Sáu byte đầu được lưu nguyên dạng hex và các giá trị big-endian trong `ms-index.json`, nhưng **chưa gán ý nghĩa** vì chưa xác minh được cấu trúc header.

Trong các script khởi tạo cảnh, ba trường lặp lại đã được nhận diện bằng đối chiếu dữ liệu: `009` chứa tên hiển thị; `002` chứa đường dẫn `.map`; `013` chứa bộ ba tọa độ xuất hiện `x,y,direction`. Bộ chỉ mục tìm thấy **127 định nghĩa cảnh**. Có **126 cảnh** trỏ tới map hiện có trong JAR; một script (`script/5012.ms`, tên `Vô Giới Chi Thế`) tham chiếu `5012.map` nhưng file map đó không có trong gói hiện tại, nên không đưa vào danh sách cảnh có thể mở trong prototype. Script `00.ms` trỏ `/00.map` được đối chiếu với map `0.map` theo ID số.

`tools/parse_ms.py` thống kê opcode theo từng file và toàn bộ tập script, không tự suy diễn ý nghĩa cho opcode chưa xác minh. Mặc định index chỉ lưu metadata gọn; thêm `--include-commands` để xuất từng token thô vào JSON khi cần phân tích sâu hơn. `game-prototype.html` hiện có dropdown **Cảnh gốc**: chọn cảnh sẽ nạp đúng map và tọa độ spawn từ script, còn dropdown **Map** dùng để duyệt map độc lập. Đây là bước tích hợp dữ liệu cảnh; chưa phải interpreter thực thi đầy đủ các lệnh script như NPC, hội thoại, điều kiện, nhiệm vụ hay chuyển cảnh.

## 4. Định dạng `.map` — PARSER ĐÃ KIỂM THỬ 124/124

Đọc theo `java.io.DataInputStream`, big-endian:

1. Hai `short` đầu (`101`, `102` trong các map đã kiểm tra).
2. `UTF` tên tileset (ví dụ `map3.png`).
3. `short rows`, `short columns`.
4. Hai `byte` kích thước tile (trong bộ dữ liệu này là 32 × 32).
5. Ma trận byte thứ nhất, `rows × columns`.
6. Ma trận byte thứ hai, cùng kích thước; được renderer sử dụng làm mã transform.
7. `short staticCount`; mỗi static entry gồm hai chuỗi UTF (`rect_data`, `metadata`).
8. `short objectCount`; mỗi object gồm `short x`, `short y`, `UTF descriptor`.

**Kết quả kiểm tra:** parser đọc hết dữ liệu, không dư byte và không lỗi với cả **124/124 map**.

Trong `lx.game.e`, giá trị tile bằng 0 là bỏ qua; giá trị khác 0 dùng `abs(value) - 1` làm tile index. Tile được lấy từ tileset theo số cột `image.width / tileWidth`. Ma trận transform truyền vào hàm vẽ vùng ảnh. Mã transform `2` là lật ngang; cách ánh xạ được đối chiếu với nhánh Nokia `DirectGraphics` trong `lx.game.af`.

Ví dụ dữ liệu:

| Map | Tileset | Lưới | Kích thước thế giới | Static | Object |
|---|---|---:|---:|---:|---:|
| `0` | `map3.png` | 10 × 27 | 864 × 320 | 0 | 0 |
| `1` | `map3.png` | 10 × 37 | 1.184 × 320 | 0 | 30 |
| `2` | `map1.png` | 10 × 37 | 1.184 × 320 | 0 | 33 |
| `101` | `map1.png` | 10 × 26 | 832 × 320 | 1 | 47 |
| `201` | `map2.png` | 10 × 26 | 832 × 320 | 1 | 38 |

`viewer/index.html` là bản xem offline độc lập, nhúng dữ liệu 124 map và 5 tileset. Viewer có chọn map, zoom, bật/tắt lưới, bật/tắt dấu đối tượng và danh sách descriptor theo tọa độ. Các marker chỉ thể hiện vị trí khai báo, chưa phải sprite thực tế.

## 5. Định dạng `.act` — ĐÃ PHÂN TÍCH LXA2, CÒN LEGACY

`lx.game.ar` là bộ đọc animation. Nhánh định dạng mới nhận diện magic `LXA2`, sau đó đọc:

- Danh sách ảnh atlas liên quan.
- Các rectangle vùng cắt sprite.
- Nhóm animation: bounds, số frame và dữ liệu từng frame.
- Các sequence tham chiếu đến animation group.
- Dữ liệu phụ trợ theo từng animation group (nếu có).

Kết quả kiểm kê 123 file:

- 106 file có magic `LXA2`.
- 17 file thuộc định dạng legacy.
- Parser hiện đọc trọn vẹn **110/123** file; 13 file legacy còn byte cuối chưa được giải nghĩa. Những byte đó được giữ nguyên dạng hex trong `analysis/act-index.json`, không bị vứt bỏ.

Ví dụ `sunwk.act` dùng `sunwk.png` và `sunwk1.png`, có 96 rectangle, 154 animation group và 50 sequence. Đây là nguồn chính để dựng sprite sheet và chuyển động Tôn Ngộ Không. Chưa khẳng định mọi animation đã được render đúng cho tới khi kiểm tra mapping và đồng bộ frame/duration trong engine mới.

## 6. Các class quan trọng đã nhận diện

- `lx.game.XMidlet`: điểm vào MIDlet.
- `lx.game.af`: lớp điều phối/tài nguyên; đọc `.ms`, phân tích `.map`, có helper vẽ vùng ảnh.
- `lx.game.ar`: đọc `.act` và cấu trúc animation.
- `lx.game.e`: render tilemap từ tileset + hai ma trận byte.
- `lx.game.m`: lớp sprite kế thừa logic từ `lx.game.ar`.

Các bản dump `javap` của 77 class được lưu tại `analysis/bytecode/` để tra cứu tiếp. Tên biến/lớp bị rút gọn hoặc obfuscate, nên cần đối chiếu luồng gọi thay vì suy đoán tên từ ký hiệu.

## 7. Runtime prototype đã dùng asset gốc

`game-prototype.html` là bản dựng Canvas 320 × 240 có thể chạy trực tiếp:

- Chọn 126 cảnh có map tương ứng với tên cảnh và tọa độ xuất hiện từ script `.ms`, hoặc duyệt map riêng trong danh sách 124 map.
- Vẽ tile theo index và transform trong dữ liệu `.map`, cuộn camera theo nhân vật.
- Ghép Tôn Ngộ Không từ hai atlas bằng rectangle và frame offset trong `sunwk.act`.
- Dùng sequence 1 (8 group) khi di chuyển; dùng group đầu sequence 0 khi đứng yên.
- Hiển thị marker object từ descriptor/toạ độ gốc trong map.

Phần input di chuyển, tốc độ, giới hạn biên và camera hiện là runtime thử nghiệm để kiểm tra dữ liệu. Chưa khẳng định chúng trùng với vật lý/chuyển động trong bản Java ME. Chưa có collision, AI, combat, skill, quest hoặc script interpreter. Bản `viewer/sprites.html` cung cấp công cụ xem ACT độc lập; cách ghép parts đã được kiểm tra trực quan trên sequence chạy của Sun Wukong, nhưng chưa mô phỏng hết logic đổi hướng của class `lx.game.m`.

## 8. Việc đã tạo trong gói nền tảng

- `tools/tdck_unpack.py`: giải nén, XOR `.ms`, trích xuất asset, phân tích map, ACT và script, xuất JSON index.
- `tools/parse_ms.py`: lập chỉ mục token/opcode và trường khởi tạo cảnh từ script `.ms`.
- `tools/build_viewer.py`: tạo viewer HTML tự chứa, chạy offline.
- `tools/render_map_preview.py`: render ảnh preview map bằng PIL.
- `tools/build_sprite_viewer.py`: tạo viewer animation ACT dùng được offline.
- `tools/build_game_prototype.py`: tạo runtime prototype Canvas có thể di chuyển qua các map.
- `tools/verify_build.py`: kiểm tra số lượng tài nguyên và tính hợp lệ các tham chiếu.
- `build/raw/`: cây file trích từ JAR, bao gồm class và tài nguyên gốc.
- `build/assets/`: nhóm tài nguyên map, sprite, data và script đã XOR.
- `build/analysis/`: index JSON cho map, ACT, script và inventory.
- `previews/`: ảnh tileset, sprite atlas và map preview.

## 9. Phần chưa hoàn thành / thứ tự nghiên cứu tiếp

1. Phân tích 10 file `.dat` và cách các class nạp bảng nhiệm vụ, kỹ năng, vật phẩm, chỉ số.
2. Xây parser semantic cho script `.ms` (header, opcode, điều kiện, biến, gọi script, lời thoại).
3. Giải nghĩa 13 file `.act` legacy còn byte dư.
4. Tìm các class xử lý va chạm, di chuyển, AI quái, sát thương, rơi vật phẩm, quest progression và lưu game.
5. Viết bộ runtime Phaser 3/JavaScript dùng dữ liệu thực; sau đó mới so sánh từng cảnh trong game gốc để tinh chỉnh.

**Kết luận trạng thái:** đã có nền tảng trích xuất/đọc dữ liệu được kiểm chứng cho map và phần lớn animation, cùng runtime thử nghiệm chạy bằng tài nguyên thật. Chưa phải bản clone chơi hoàn chỉnh; gameplay và interpreter script vẫn là các phần cần reverse-engineer tiếp.

## 10. Đợt phân tích `.dat` — parser cấu trúc nhị phân bước đầu

Đã kiểm kê và đọc được đủ **10/10 bảng `.dat`** trong JAR: `ach`, `armEx1`, `armEx2`, `attack`, `exception`, `exp`, `goods`, `mission`, `skill`, `sprite`.

### Header chung quan sát được

Các file đều có cấu trúc đầu file nhất quán:

1. `u16` big-endian: `tableMarker` (giữ nguyên, chưa gán ý nghĩa nghiệp vụ).
2. `u16` big-endian: số record.
3. `u8`: số field.
4. Mảng descriptor, mỗi field một mã kiểu dữ liệu.
5. Các record nhị phân liên tiếp theo thứ tự descriptor.

Các mã kiểu xuất hiện trong 10 file là `1`, `2`, `4`; parser đang đọc lần lượt thành signed byte, signed short big-endian và signed int big-endian. Kích thước record được suy ra bằng tổng kích thước các kiểu.

### Kết quả đã xác minh mạnh

- `exp.dat`: marker `2`, 200 record, 2 field `[2, 4]`; phần record chiếm chính xác 1.200/1.200 byte sau header. Các dòng đầu là `[level=1, exp=25]`, `[2,40]`, `[3,65]`; không còn trailer. Đây là bảng có thể parse trọn vẹn theo cấu trúc hiện tại.
- Chín bảng còn lại đều parse được phần record cố định mà không vượt kích thước file; tuy nhiên còn trailer dữ liệu phía sau. Trailer có nội dung UTF-8 và dấu `;` ở nhiều bảng (ví dụ tên/mô tả nhiệm vụ, kỹ năng, vật phẩm, thành tựu, trạng thái và nhân vật), nhưng ranh giới giữa các nhóm chuỗi/chỉ số tham chiếu chưa được giải nghĩa.

### Công cụ và đầu ra

- `tools/parse_dat.py`: đọc header, descriptor, record và giữ nguyên trailer; từ chối mã kiểu chưa biết thay vì tự đoán.
- `analysis/dat-index.json`: dữ liệu xuất từ cả 10 bảng, gồm record dạng mảng, metadata, trailer thô dạng UTF-8 để tra cứu.

**Giới hạn quan trọng:** `tableMarker` chưa được gán tên bảng theo logic game; các vị trí trong record chưa được đặt tên thành `id`, `name`, `damage`, `price`, v.v. Các đoạn text UTF-8 là góc nhìn phục vụ điều tra, không phải khẳng định đã giải mã xong string table. Bước kế tiếp là truy vết nơi game nạp `/data/` và đối chiếu cách các record được truy cập trong bytecode, sau đó mới đặt tên field và liên kết chuỗi.
