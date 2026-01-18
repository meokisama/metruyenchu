#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Source implementation for metruyenhot.me
"""

import re
import html
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from sources.base import BaseNovelSource
from config import DEFAULT_HEADERS, DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES, DEFAULT_DELAY_BETWEEN_REQUESTS


class MetruyenhotMeSource(BaseNovelSource):
    """Source implementation for metruyenhot.me"""

    name = "metruyenhot.me"
    base_url = "https://metruyenhot.me"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def parse_novel_url(self, url):
        """
        Parse novel URL to extract all novel information

        Args:
            url: Full URL of the novel page (e.g., https://metruyenhot.me/tu-hai-nhi-bat-dau-nhap-dao)

        Returns:
            dict with novel information
        """
        print(f"\nĐang phân tích URL: {url}")

        # Parse URL to get base_url and novel_slug
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        novel_slug = parsed_url.path.strip('/').split('/')[-1]

        print(f"✓ Base URL: {base_url}")
        print(f"✓ Novel slug: {novel_slug}")

        # Fetch the novel page
        try:
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title from h1.title or .wrap-detail h1
            novel_title = ""
            title_tag = soup.select_one('.wrap-detail h1.title a')
            if title_tag:
                novel_title = html.unescape(title_tag.get_text(strip=True))
            else:
                title_tag = soup.select_one('h1.title')
                if title_tag:
                    novel_title = html.unescape(title_tag.get_text(strip=True))
                else:
                    novel_title = novel_slug.replace('-', ' ').title()

            print(f"✓ Tiêu đề: {novel_title}")

            # Extract author from span[itemprop="author"]
            novel_author = ""
            author_tag = soup.select_one('span[itemprop="author"]')
            if author_tag:
                novel_author = author_tag.get_text(strip=True)
            else:
                novel_author = "Không rõ"

            print(f"✓ Tác giả: {novel_author}")

            # Extract description from span[itemprop="description"]
            novel_description = ""
            desc_tag = soup.select_one('span[itemprop="description"]')
            if desc_tag:
                novel_description = desc_tag.get_text(separator='\n', strip=True)
            else:
                # Try to get from .content1
                desc_div = soup.select_one('.content1')
                if desc_div:
                    novel_description = desc_div.get_text(separator='\n', strip=True)[:500]

            # Extract cover image from .wrap-detail img[data-src]
            cover_image = None
            cover_tag = soup.select_one('.wrap-detail img[data-src]')
            if cover_tag and cover_tag.get('data-src'):
                cover_url = cover_tag.get('data-src')
                if not cover_url.startswith('http'):
                    cover_url = urljoin(base_url, cover_url)
                try:
                    print(f"✓ Đang tải ảnh bìa...", end=' ')
                    cover_response = self.session.get(cover_url, timeout=DEFAULT_TIMEOUT)
                    cover_response.raise_for_status()
                    cover_image = cover_response.content
                    print("✓")
                except Exception as e:
                    print(f"✗ ({e})")

            # Extract total chapters from "Chuong Moi Nhat" section
            # Find the first link in that section with pattern /novel-slug/chuong-XXX/
            total_chapters = None

            # Method 1: Find link in "Chuong Moi Nhat" section
            latest_section = soup.find('h3', string=re.compile(r'Chương Mới Nhất', re.I))
            if latest_section:
                parent = latest_section.find_parent('div', class_='row') or latest_section.find_parent('div')
                if parent:
                    links = parent.find_all('a', href=re.compile(r'/chuong-\d+'))
                    if links:
                        # Get the first link which should be the latest chapter
                        href = links[0].get('href', '')
                        chapter_match = re.search(r'/chuong-(\d+)', href)
                        if chapter_match:
                            total_chapters = int(chapter_match.group(1))

            # Method 2: Find from pagination - look for the last page number
            if not total_chapters:
                pagination = soup.select_one('.pagination')
                if pagination:
                    # Find all links with page numbers
                    page_links = pagination.find_all('a', href=re.compile(r'\?page=\d+'))
                    max_page = 1
                    for link in page_links:
                        page_match = re.search(r'\?page=(\d+)', link.get('href', ''))
                        if page_match:
                            page_num = int(page_match.group(1))
                            if page_num > max_page:
                                max_page = page_num
                    # Each page has ~50 chapters, estimate total
                    if max_page > 1:
                        total_chapters = max_page * 50  # Rough estimate

            # Method 3: Search in page text
            if not total_chapters:
                chapter_match = re.search(r'chuong-(\d+)', response.text, re.I)
                if chapter_match:
                    # Find highest chapter number in page
                    all_chapters = re.findall(r'/chuong-(\d+)', response.text)
                    if all_chapters:
                        total_chapters = max(int(c) for c in all_chapters)

            if not total_chapters:
                raise ValueError("Không tìm thấy số chương trong trang")

            print(f"✓ Tổng số chương: {total_chapters}")

            # Extract novel_id if available (from hidden input or script)
            novel_id = None
            # Try to find story_id in page
            story_id_match = re.search(r'storyId["\s:=]+["\']?(\d+)', response.text)
            if story_id_match:
                novel_id = int(story_id_match.group(1))
            else:
                # Use slug hash as ID
                novel_id = hash(novel_slug) % 100000

            return {
                'base_url': base_url,
                'novel_slug': novel_slug,
                'novel_id': novel_id,
                'novel_title': novel_title,
                'novel_author': novel_author,
                'novel_description': novel_description,
                'cover_image': cover_image,
                'max_pages': None,  # Will be calculated during chapter list fetch
                'total_chapters': total_chapters
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi tải trang: {e}")
        except Exception as e:
            raise Exception(f"Lỗi khi phân tích trang: {e}")

    def get_chapter_list(self, novel_info, delay=0.5):
        """
        Fetch list of all chapters

        For metruyenhot.me, chapters are numbered sequentially from 1 to total_chapters.
        URL pattern: /novel-slug/chuong-X/

        Args:
            novel_info: Dict containing novel information from parse_novel_url
            delay: Delay time between requests (seconds)

        Returns:
            List of dicts containing chapter information
        """
        chapters = []
        base_url = novel_info['base_url']
        novel_slug = novel_info['novel_slug']
        total_chapters = novel_info['total_chapters']

        print(f"\nĐang tạo danh sách {total_chapters} chương...")

        # For metruyenhot.me, we can generate chapter URLs directly
        # since they follow pattern: /novel-slug/chuong-X/
        for i in range(1, total_chapters + 1):
            chapter_url = f"{base_url}/{novel_slug}/chuong-{i}/"
            chapter_info = {
                'title': f"Chương {i}",
                'url': chapter_url,
                'slug': f"chuong-{i}"
            }
            chapters.append(chapter_info)

        print(f"✓ Tổng cộng {len(chapters)} chương")
        return chapters

    def get_chapter_content(self, chapter_url):
        """
        Fetch content of a chapter

        Args:
            chapter_url: URL of the chapter

        Returns:
            String containing chapter content (HTML)
        """
        response = self.session.get(chapter_url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Update chapter title from page
        title_tag = soup.select_one('.rv-chapt-title h2 a')
        if title_tag:
            chapter_title = title_tag.get_text(strip=True)

        # Find content div - priority order
        content_div = soup.select_one('.chapter-c') or \
                     soup.select_one('.book-list.full-story.content.chapter-c') or \
                     soup.select_one('#j_content')

        if not content_div:
            raise ValueError("Không tìm thấy nội dung chương")

        # Clean content
        # Remove script, style tags
        for tag in content_div.find_all(['script', 'style', 'ins', 'iframe']):
            tag.decompose()

        # Remove ads divs
        for tag in content_div.find_all('div', id=re.compile(r'ads|banner', re.I)):
            tag.decompose()
        for tag in content_div.find_all('div', class_=re.compile(r'ads|banner', re.I)):
            tag.decompose()

        # Get all paragraph content
        paragraphs = content_div.find_all('p')
        if paragraphs:
            content_parts = []
            for p in paragraphs:
                p_html = str(p)
                # Convert <br> to paragraph breaks
                p_html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', p_html, flags=re.I)
                p_html = re.sub(r'<br\s*/?>', '</p><p>', p_html, flags=re.I)
                content_parts.append(p_html)
            content_html = '\n'.join(content_parts)
        else:
            # Fallback: get all text
            content_html = str(content_div)
            # Process <br> tags
            content_html = re.sub(r'(<br\s*/?>){2,}', '</p><p>', content_html, flags=re.I)
            content_html = re.sub(r'<br\s*/?>', '</p><p>', content_html, flags=re.I)

        return f"<div>{content_html}</div>"

    def crawl_all_chapters(self, chapters, delay=None, max_retries=None):
        """
        Crawl content of all chapters, also fetch real chapter titles

        Args:
            chapters: List of chapters
            delay: Delay time between requests
            max_retries: Number of retries on error

        Returns:
            List of dicts containing chapter information and content
        """
        if delay is None:
            delay = DEFAULT_DELAY_BETWEEN_REQUESTS
        if max_retries is None:
            max_retries = DEFAULT_MAX_RETRIES

        print(f"\nĐang crawl nội dung {len(chapters)} chương...")

        for idx, chapter in enumerate(chapters, 1):
            retries = 0
            success = False

            while retries < max_retries and not success:
                try:
                    if retries == 0:
                        print(f"  [{idx}/{len(chapters)}] {chapter['title']}...", end=' ')

                    response = self.session.get(chapter['url'], timeout=DEFAULT_TIMEOUT)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Update chapter title from page
                    title_tag = soup.select_one('.rv-chapt-title h2 a')
                    if title_tag:
                        chapter['title'] = title_tag.get_text(strip=True)

                    # Get content
                    content_div = soup.select_one('.chapter-c') or \
                                 soup.select_one('#j_content')

                    if not content_div:
                        raise ValueError("Không tìm thấy nội dung")

                    # Clean content
                    for tag in content_div.find_all(['script', 'style', 'ins', 'iframe']):
                        tag.decompose()
                    for tag in content_div.find_all('div', id=re.compile(r'ads|banner', re.I)):
                        tag.decompose()
                    for tag in content_div.find_all('div', class_=re.compile(r'ads|banner', re.I)):
                        tag.decompose()

                    # Get paragraphs
                    paragraphs = content_div.find_all('p')
                    if paragraphs:
                        content_parts = []
                        for p in paragraphs:
                            p_html = str(p)
                            p_html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', p_html, flags=re.I)
                            p_html = re.sub(r'<br\s*/?>', '</p><p>', p_html, flags=re.I)
                            content_parts.append(p_html)
                        chapter['content'] = f"<div>{''.join(content_parts)}</div>"
                    else:
                        content_html = str(content_div)
                        content_html = re.sub(r'(<br\s*/?>){2,}', '</p><p>', content_html, flags=re.I)
                        content_html = re.sub(r'<br\s*/?>', '</p><p>', content_html, flags=re.I)
                        chapter['content'] = f"<div>{content_html}</div>"

                    print(f"✓ {chapter['title']}")
                    success = True
                    time.sleep(delay)

                except Exception as e:
                    retries += 1
                    error_msg = str(e)
                    if retries < max_retries:
                        print(f"✗ ({error_msg}) - Thử lại {retries}/{max_retries}...", end=' ')
                        time.sleep(delay * 2)
                    else:
                        print(f"✗ Bỏ qua ({error_msg})")
                        chapter['content'] = f"<p>Lỗi khi tải chương sau {max_retries} lần thử: {error_msg}</p>"

        return chapters
