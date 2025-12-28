#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import html
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config import DEFAULT_HEADERS, DEFAULT_TIMEOUT


class NovelScraper:
    """Class for scraping novel content from websites"""

    def __init__(self, base_url, novel_slug, novel_id,
                 novel_title="", novel_author="", novel_description="", cover_image=None, headers=None):
        """
        Initialize the scraper

        Args:
            base_url: Base URL of the website (e.g., https://metruyenchu.com.vn)
            novel_slug: Novel slug in URL (e.g., 'nuong-tu-dung-la-nu-ma-dau')
            novel_id: Novel ID for fetching chapter list (e.g., 60240)
            novel_title: Novel title (optional)
            novel_author: Novel author (optional)
            novel_description: Novel description (optional)
            cover_image: Cover image bytes (optional)
            headers: Custom headers for requests (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.novel_slug = novel_slug
        self.novel_id = novel_id
        self.session = requests.Session()
        self.headers = headers or DEFAULT_HEADERS
        self.session.headers.update(self.headers)

        # Metadata
        self.novel_title = novel_title
        self.novel_author = novel_author
        self.novel_description = novel_description
        self.cover_image = cover_image

    def get_chapter_list(self, delay=0.5, max_pages=None):
        """
        Fetch list of all chapters

        Args:
            delay: Delay time between requests (seconds)
            max_pages: Maximum number of pages to fetch (None for all pages)

        Returns:
            List of dicts containing chapter information
        """
        chapters = []
        page = 1

        if max_pages:
            print(f"\nĐang lấy danh sách chương (tối đa {max_pages} trang)...")
        else:
            print("\nĐang lấy danh sách chương...")

        while True:
            # Check if reached max pages
            if max_pages and page > max_pages:
                print(f"(Đã đạt giới hạn {max_pages} trang)")
                break
            try:
                url = f"{self.base_url}/get/listchap/{self.novel_id}?page={page}"
                print(f"  Trang {page}...", end=' ')

                response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                data = response.json()

                # Check if there is data
                if not data.get('data'):
                    print("(Hết)")
                    break

                # Unescape HTML entities
                html_content = html.unescape(data['data'])
                soup = BeautifulSoup(html_content, 'html.parser')

                # Find all chapter links
                links = soup.find_all('a', href=True)

                if not links:
                    print("(Hết)")
                    break

                page_chapters = []
                for link in links:
                    href = link.get('href', '')

                    # Only get chapter links with correct pattern
                    # Chapter URLs: /novel-slug/chuong-XX-XXXXX
                    if not href or 'javascript:' in href:
                        continue

                    # Check if href contains 'chuong-' pattern
                    if '/chuong-' not in href.lower():
                        continue

                    chapter_info = {
                        'title': link.get_text(strip=True),
                        'url': urljoin(self.base_url, href),
                        'slug': href.split('/')[-1] if '/' in href else href
                    }
                    page_chapters.append(chapter_info)

                chapters.extend(page_chapters)
                print(f"✓ Tìm thấy {len(page_chapters)} chương")

                page += 1
                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                print(f"\n✗ Lỗi khi lấy trang {page}: {e}")
                break
            except Exception as e:
                print(f"\n✗ Lỗi không xác định trang {page}: {e}")
                break

        print(f"\n✓ Tổng cộng tìm thấy {len(chapters)} chương")
        return chapters

    def get_chapter_content(self, chapter_url):
        """
        Fetch content of a chapter

        Args:
            chapter_url: URL of the chapter

        Returns:
            String containing chapter content (HTML)
        """
        try:
            response = self.session.get(chapter_url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find div containing content - in order of priority
            content_div = soup.find('div', class_='truyen') or \
                         soup.find('div', id='chapter-content') or \
                         soup.find('div', class_='chapter-content') or \
                         soup.find('div', id='content')

            if content_div:
                # Clean content
                # Remove script, style tags
                for tag in content_div.find_all(['script', 'style']):
                    tag.decompose()

                # Remove comments and ads if any
                for tag in content_div.find_all(['iframe', 'ins']):
                    tag.decompose()

                # Get HTML content
                content_html = str(content_div)

                # Process <br> tags to create paragraphs
                # Convert consecutive <br> to </p><p>
                content_html = re.sub(r'(<br\s*/?>){2,}', '</p><p>', content_html, flags=re.IGNORECASE)
                # Convert single <br> to </p><p>
                content_html = re.sub(r'<br\s*/?>', '</p><p>', content_html, flags=re.IGNORECASE)

                # Wrap in div and ensure p tags exist
                if '<p>' not in content_html.lower():
                    # If no p tag, wrap text in p
                    soup_content = BeautifulSoup(content_html, 'html.parser')
                    text_content = soup_content.get_text()
                    paragraphs = [f"<p>{para.strip()}</p>" for para in text_content.split('\n') if para.strip()]
                    content_html = '\n'.join(paragraphs)

                return f"<div>{content_html}</div>"
            else:
                return "<p>Không tìm thấy nội dung chương.</p>"

        except Exception as e:
            print(f"\n    ✗ Lỗi: {e}")
            return f"<p>Lỗi khi tải chương: {e}</p>"

    def crawl_all_chapters(self, chapters, delay=1.0, max_retries=3):
        """
        Crawl content of all chapters

        Args:
            chapters: List of chapters
            delay: Delay time between requests
            max_retries: Number of retries on error

        Returns:
            List of dicts containing chapter information and content
        """
        print(f"\nĐang crawl nội dung {len(chapters)} chương...")

        for idx, chapter in enumerate(chapters, 1):
            retries = 0
            success = False

            while retries < max_retries and not success:
                try:
                    print(f"  [{idx}/{len(chapters)}] {chapter['title']}...", end=' ')

                    content = self.get_chapter_content(chapter['url'])
                    chapter['content'] = content

                    print("✓")
                    success = True
                    time.sleep(delay)

                except Exception as e:
                    retries += 1
                    if retries < max_retries:
                        print(f"✗ (Thử lại {retries}/{max_retries})...", end=' ')
                        time.sleep(delay * 2)
                    else:
                        print(f"✗ Bỏ qua")
                        chapter['content'] = f"<p>Lỗi khi tải chương sau {max_retries} lần thử.</p>"

        return chapters
