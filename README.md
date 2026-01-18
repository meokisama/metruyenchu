# Truyện Chữ

Tải truyện từ nhiều nguồn và chuyển đổi sang EPUB.

## Nguồn hỗ trợ

- metruyenchu.com.vn
- metruyenhot.me

## Cài đặt

```bash
uv sync
```

## Sử dụng

```bash
uv run main.py
```

1. Chọn nguồn truyện
2. Nhập URL truyện
3. Chọn phạm vi chương (tất cả hoặc từ X đến Y)
4. Xác nhận để bắt đầu tải

## Cấu hình

Tùy chỉnh trong `config.py`:

| Tham số                          | Mặc định | Mô tả                  |
| -------------------------------- | -------- | ---------------------- |
| `DEFAULT_DELAY_BETWEEN_REQUESTS` | 1.0s     | Delay giữa các request |
| `DEFAULT_MAX_RETRIES`            | 3        | Số lần retry khi lỗi   |
| `DEFAULT_TIMEOUT`                | 30s      | Timeout cho request    |
