#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scraper import NovelScraper
from epub_creator import EpubCreator
from novel_parser import parse_novel_url
from config import DEFAULT_DELAY_BETWEEN_REQUESTS


def main():
    print("=" * 60)
    print("METRUYENCHU SCRAPER")
    print("=" * 60)

    novel_url = input("\nNhập link truyện: ").strip()
    if not novel_url:
        print("✗ URL không hợp lệ!")
        return

    try:
        novel_info = parse_novel_url(novel_url)
    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
        return

    try:
        scraper = NovelScraper(
            base_url=novel_info['base_url'],
            novel_slug=novel_info['novel_slug'],
            novel_id=novel_info['novel_id'],
            novel_title=novel_info['novel_title'],
            novel_author=novel_info['novel_author'],
            novel_description=novel_info['novel_description'],
            cover_image=novel_info['cover_image']
        )

        chapters = scraper.get_chapter_list(
            delay=0.5,
            max_pages=novel_info['max_pages']
        )

        if not chapters:
            print("\n✗ Không tìm thấy chương nào!")
            return

        # Ask user for chapter range
        total_chapters = len(chapters)
        print(f"\n✓ Tìm thấy {total_chapters} chương")
        print("\nChọn phạm vi chương:")
        print("  1. Lấy tất cả chương")
        print("  2. Lấy từ chương X đến chương Y")

        choice = input("\nLựa chọn (1/2): ").strip()

        if choice == '2':
            while True:
                try:
                    start_input = input(f"Từ chương (1-{total_chapters}): ").strip()
                    end_input = input(f"Đến chương (1-{total_chapters}): ").strip()

                    start_chapter = int(start_input) if start_input else 1
                    end_chapter = int(end_input) if end_input else total_chapters

                    if start_chapter < 1 or start_chapter > total_chapters:
                        print(f"✗ Chương bắt đầu phải từ 1 đến {total_chapters}")
                        continue
                    if end_chapter < 1 or end_chapter > total_chapters:
                        print(f"✗ Chương kết thúc phải từ 1 đến {total_chapters}")
                        continue
                    if start_chapter > end_chapter:
                        print(f"✗ Chương bắt đầu không được lớn hơn chương kết thúc")
                        continue

                    # Filter chapters
                    chapters = chapters[start_chapter-1:end_chapter]
                    print(f"\n✓ Đã chọn: Chương {start_chapter} đến {end_chapter} ({len(chapters)} chương)")
                    break
                except ValueError:
                    print("✗ Vui lòng nhập số hợp lệ")

        print(f"\nSẵn sàng crawl {len(chapters)} chương.")
        response = input("Tiếp tục? (y/n): ").strip().lower()
        if response != 'y':
            print("Đã hủy.")
            return

        chapters_with_content = scraper.crawl_all_chapters(
            chapters,
            delay=DEFAULT_DELAY_BETWEEN_REQUESTS
        )

        epub_creator = EpubCreator(
            novel_title=scraper.novel_title,
            novel_author=scraper.novel_author,
            novel_id=scraper.novel_id,
            novel_description=scraper.novel_description,
            cover_image=scraper.cover_image
        )
        output_file = epub_creator.create_epub(chapters_with_content)

        print("\n" + "=" * 60)
        print("✓ HOÀN THÀNH!")
        print(f"✓ File đã được lưu: {output_file}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n✗ Đã dừng bởi người dùng.")
    except Exception as e:
        print(f"\n✗ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
