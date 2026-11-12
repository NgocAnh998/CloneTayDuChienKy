# TDCK Reverse Engineering

Tài liệu và công cụ phân tích JAR Tây Du Chiến Ký gốc.

## Đã xác minh
- `.ms`: XOR từng byte với `0x01` theo bytecode `lx.game.af`.
- `.map`: parser big-endian, đã kiểm tra đọc hết 124/124 bản đồ.
- `.act`: định dạng LXA2 và legacy; parser hiện đọc hết 110/123 file, giữ byte đuôi chưa hiểu trong JSON.
- Báo cáo chi tiết: [REVERSE_ENGINEERING_REPORT.md](REVERSE_ENGINEERING_REPORT.md).

## Chạy công cụ
Yêu cầu Python 3.10+:

```powershell
python tools/tdck_unpack.py .\TDCK-HBTG-320x240.jar --out .\build
```

Công cụ trích xuất cây JAR, giải XOR các script MS và xuất index JSON cho map/ACT. JAR gốc không được commit vào repository; hãy đặt file JAR của bạn ở thư mục gốc hoặc truyền đường dẫn tuyệt đối.

## Trạng thái
Đây là nền tảng reverse-engineering, chưa phải bản clone hoàn chỉnh. Chưa có interpreter MS, giải mã DAT, collision, AI, combat, quest hoặc save-game runtime.
