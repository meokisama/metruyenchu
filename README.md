# MeTruyenChu Scraper

Công cụ tải truyện từ [metruyenchu.com.vn](https://metruyenchu.com.vn) và chuyển đổi sang định dạng EPUB để đọc offline.

## Tính năng

- Tự động phân tích URL và lấy thông tin truyện
- Tải tất cả chương hoặc chọn phạm vi chương cụ thể
- Chuyển đổi sang định dạng EPUB với đầy đủ metadata
- Tải và nhúng ảnh bìa truyện
- Cơ chế retry tự động khi gặp lỗi mạng
- Delay giữa các request để tránh quá tải server
- Hiển thị tiến trình chi tiết trong quá trình tải

## Cài đặt

1. Clone repository:

```bash
git clone <repository-url>
cd metruyenchu
```

2. Cài đặt dependencies bằng uv:

```bash
uv sync
```

## Sử dụng

Chạy script chính:

```bash
uv run main.py
```

Script sẽ yêu cầu:

1. **Nhập URL truyện**: Dán link truyện từ metruyenchu.com.vn

   - Ví dụ: `https://metruyenchu.com.vn/nuong-tu-dung-la-nu-ma-dau`

2. **Chọn phạm vi chương**:

   - Tùy chọn 1: Tải tất cả chương
   - Tùy chọn 2: Tải từ chương X đến chương Y

3. **Xác nhận**: Nhập `y` để bắt đầu tải

File EPUB sẽ được lưu trong thư mục hiện tại với tên dạng `Ten_Truyen.epub`.

## Cấu hình

Các cấu hình có thể tùy chỉnh trong `config.py`:

- `DEFAULT_DELAY_BETWEEN_REQUESTS`: Thời gian delay giữa các request (mặc định: 1.0s)
- `DEFAULT_CHAPTER_LIST_DELAY`: Delay khi lấy danh sách chương (mặc định: 0.5s)
- `DEFAULT_MAX_RETRIES`: Số lần retry khi lỗi (mặc định: 3)
- `DEFAULT_TIMEOUT`: Timeout cho mỗi request (mặc định: 30s)
- `CHAPTERS_PER_PAGE`: Số chương trên mỗi trang (mặc định: 100)
- `EPUB_CSS_STYLE`: CSS cho file EPUB
