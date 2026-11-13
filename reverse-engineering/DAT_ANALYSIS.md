# DAT reverse-engineering — Tây Du Chiến Ký

Đã kiểm kê và parse phần record cố định của đủ 10 file trong `build/raw/data/`: ach.dat, armEx1.dat, armEx2.dat, attack.dat, exception.dat, exp.dat, goods.dat, mission.dat, skill.dat và sprite.dat.

## Cấu trúc chung quan sát được

- 2 byte big-endian: table marker (chưa biết ý nghĩa nghiệp vụ).
- 2 byte big-endian: số record.
- 1 byte: số field.
- Tiếp theo là một descriptor cho mỗi field.
- Các record fixed-width theo thứ tự descriptor.

Type code xuất hiện: 1 = signed byte, 2 = signed big-endian short, 4 = signed big-endian int. Các độ rộng này khớp với phần record cố định của cả 10 bảng.

## Bảng đã parse

| File | Marker | Records | Fields | Bytes/record | Trailer bytes |
|---|---:|---:|---:|---:|---:|
| ach.dat | 21 | 32 | 19 | 29 | 4085 |
| armEx1.dat | 7 | 5 | 6 | 8 | 403 |
| armEx2.dat | 4 | 8 | 3 | 4 | 258 |
| attack.dat | 20 | 21 | 19 | 20 | 982 |
| exception.dat | 19 | 19 | 17 | 18 | 2088 |
| exp.dat | 2 | 200 | 2 | 6 | 0 |
| goods.dat | 33 | 208 | 31 | 47 | 5706 |
| mission.dat | 14 | 100 | 12 | 14 | 3178 |
| skill.dat | 14 | 80 | 12 | 15 | 6350 |
| sprite.dat | 12 | 123 | 9 | 13 | 3773 |

## exp.dat — parse trọn vẹn

`exp.dat` có 200 record, hai field kiểu short và int. Phần record chiếm chính xác 1.200 byte sau header; không còn trailer. Năm dòng đầu: `[1, 25]`, `[2, 40]`, `[3, 65]`, `[4, 100]`, `[5, 145]`. Ba dòng cuối: `[198, 39204000]`, `[199, 39601000]`, `[200, 99960000]`. Điều này rất phù hợp với cách hiểu level và EXP yêu cầu, nhưng vẫn cần xác nhận bằng class tiêu thụ bảng.

## Trailer và giới hạn

Chín bảng còn lại có trailer chứa nhiều đoạn UTF-8 tiếng Việt/Trung và chuỗi phân tách bằng dấu chấm phẩy. Có thể nhận ra tên/mô tả nhiệm vụ, kỹ năng, vật phẩm, thành tựu, trạng thái và nhân vật. Tuy nhiên ranh giới các nhóm chuỗi, prefix nhị phân, offset và liên kết chuỗi với record chưa được giải nghĩa. Parser giữ nguyên trailer và chỉ tạo góc nhìn UTF-8 để điều tra; không gán tên field hoặc khẳng định đã giải mã xong string table.

## Chạy parser

`python tools/parse_dat.py build/raw/data -o analysis/dat-index.json`

Công cụ từ chối type code lạ thay vì đoán. Bước kế tiếp là truy vết nơi game mở `/data/`, tìm class đọc từng bảng, sau đó mới gán tên field và nối ID chuỗi cho mission, skill, goods và combat.
