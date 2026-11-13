# TDCK Reverse Engineering

Tài liệu và công cụ phân tích JAR Tây Du Chiến Ký gốc.

## Đã xác minh
- `.ms`: XOR từng byte với `0x01` theo bytecode `lx.game.af`.
- `.map`: parser big-endian, đã kiểm tra đọc hết 124/124 bản đồ.
- `.act`: định dạng LXA2 và legacy; parser đọc hết 110/123 file, giữ byte đuôi chưa hiểu trong JSON.
- `.dat`: đã nhận diện header và parse phần record cố định của đủ 10/10 bảng; `exp.dat` parse trọn vẹn. Trailer của 9 bảng còn lại vẫn cần giải nghĩa.
- Báo cáo DAT: [DAT_ANALYSIS.md](DAT_ANALYSIS.md).
- Báo cáo tổng: [REVERSE_ENGINEERING_REPORT.md](REVERSE_ENGINEERING_REPORT.md).

## Chạy công cụ
Yêu cầu Python 3.10+:

```powershell
python tools/tdck_unpack.py .\TDCK-HBTG-320x240.jar --out .\build
python tools/parse_dat.py .\build\raw\data -o .\build\analysis\dat-index.json
```

Công cụ trích xuất cây JAR, giải XOR các script MS và xuất index JSON cho map/ACT. Parser DAT xuất record dạng mảng và giữ trailer để phân tích tiếp. JAR gốc không được commit vào repository; hãy đặt file JAR của bạn ở thư mục gốc hoặc truyền đường dẫn tuyệt đối.

## Trạng thái
Đây là nền tảng reverse-engineering, chưa phải bản clone hoàn chỉnh. Các phần còn lại gồm giải nghĩa trailer/string table DAT, interpreter MS, collision, AI, combat, quest và save-game runtime.
