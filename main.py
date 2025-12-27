#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scraper import NovelScraper
from epub_creator import EpubCreator
from config import DEFAULT_DELAY_BETWEEN_REQUESTS


def main():
    BASE_URL = "https://metruyenchu.com.vn"
    NOVEL_SLUG = "nuong-tu-dung-la-nu-ma-dau"
    NOVEL_ID = 60240
    OUTPUT_FILE = ""
    DELAY_BETWEEN_REQUESTS = DEFAULT_DELAY_BETWEEN_REQUESTS
    MAX_PAGES_TO_FETCH = 12 # None = fetch all pages
    START_CHAPTER = None  # None = first chapter
    END_CHAPTER = 50    # None = all chapters

    try:
        # Initialize scraper
        scraper = NovelScraper(BASE_URL, NOVEL_SLUG, NOVEL_ID)

        # Get novel information
        scraper.get_novel_info()

        # Get chapter list
        chapters = scraper.get_chapter_list(delay=0.5, max_pages=MAX_PAGES_TO_FETCH)

        if not chapters:
            print("\n✗ Không tìm thấy chương nào!")
            return

        # Filter chapters by range if configured
        total_chapters = len(chapters)
        start_idx = (START_CHAPTER - 1) if START_CHAPTER else 0
        end_idx = END_CHAPTER if END_CHAPTER else total_chapters

        # Validate range
        if start_idx < 0:
            start_idx = 0
        if end_idx > total_chapters:
            end_idx = total_chapters
        if start_idx >= end_idx:
            print(f"\n✗ Phạm vi chương không hợp lệ: {START_CHAPTER} đến {END_CHAPTER}")
            print(f"   Tổng số chương: {total_chapters}")
            return

        # Apply filter
        if START_CHAPTER or END_CHAPTER:
            chapters = chapters[start_idx:end_idx]
            print(f"\n✓ Đã lọc: Chương {start_idx + 1} đến {end_idx} (Tổng: {len(chapters)} chương)")
            print(f"   Danh sách đầy đủ có {total_chapters} chương")

        # Ask user to continue
        print(f"\nSẵn sàng crawl {len(chapters)} chương.")
        response = input("Tiếp tục? (y/n): ").strip().lower()
        if response != 'y':
            print("Đã hủy.")
            return

        # Crawl chapter content
        chapters_with_content = scraper.crawl_all_chapters(
            chapters,
            delay=DELAY_BETWEEN_REQUESTS
        )

        # Create EPUB file
        epub_creator = EpubCreator(
            novel_title=scraper.novel_title,
            novel_author=scraper.novel_author,
            novel_id=scraper.novel_id,
            novel_description=scraper.novel_description,
            cover_image=scraper.cover_image
        )
        output_file = epub_creator.create_epub(chapters_with_content, OUTPUT_FILE)

        print("\n" + "=" * 60)
        print("✓ HOÀN THÀNH!")
        print(f"✓ File đã được lưu: {output_file}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n✗ Đã dừng bởi người dùng.")
    except Exception as e:
        print(f"\n\n✗ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
