#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Source implementation for metruyenchu.com.vn
"""

import re
import math
import html
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from sources.base import BaseNovelSource
from config import DEFAULT_HEADERS, DEFAULT_TIMEOUT, CHAPTERS_PER_PAGE


class MetruyenchuComVnSource(BaseNovelSource):
    """Source implementation for metruyenchu.com.vn"""

    name = "metruyenchu.com.vn"
    base_url = "https://metruyenchu.com.vn"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def parse_novel_url(self, url):
        """
        Parse novel URL to extract all novel information

        Args:
            url: Full URL of the novel page (e.g., https://metruyenchu.com.vn/nuong-tu-dung-la-nu-ma-dau)

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

            # Extract novel ID
            novel_id = None
            script_match = re.search(r"var\s+rid\s*=\s*['\"](\d+)['\"]", response.text)
            if script_match:
                novel_id = int(script_match.group(1))

            if not novel_id:
                bid_input = soup.find('input', {'name': 'bid', 'type': 'hidden'})
                if bid_input and bid_input.get('value'):
                    novel_id = int(bid_input.get('value'))

            if not novel_id:
                raise ValueError("Không tìm thấy Novel ID trong trang")

            print(f"✓ Novel ID: {novel_id}")

            # Extract title
            novel_title = ""
            title_tag = soup.find('h1', itemprop='name') or soup.find('h1')
            if title_tag:
                novel_title = html.unescape(title_tag.get_text(strip=True))
            else:
                novel_title = novel_slug.replace('-', ' ').title()

            print(f"✓ Tiêu đề: {novel_title}")

            # Extract author
            novel_author = ""
            author_tag = soup.find('a', itemprop='author') or \
                        soup.find('a', href=re.compile(r'/tac-gia/'))
            if author_tag:
                novel_author = author_tag.get_text(strip=True)
            else:
                novel_author = "Không rõ"

            print(f"✓ Tác giả: {novel_author}")

            # Extract description
            novel_description = ""
            desc_tag = soup.find('div', itemprop='description')
            if desc_tag:
                novel_description = desc_tag.get_text(separator='\n', strip=True)

            # Extract cover image
            cover_image = None
            cover_tag = soup.find('img', itemprop='image')
            if cover_tag and cover_tag.get('src'):
                cover_url = cover_tag.get('src')
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

            # Extract total chapters
            total_chapters = None

            # Method 1: Find <b> tag containing "Số chương" then get parent <li>
            chapter_b = soup.find('b', string=re.compile(r'Số chương'))
            if chapter_b:
                chapter_li = chapter_b.parent
                if chapter_li:
                    chapter_text = chapter_li.get_text()
                    chapter_match = re.search(r'(\d+)', chapter_text)
                    if chapter_match:
                        total_chapters = int(chapter_match.group(1))

            # Method 2: Find any text containing "Số chương :" followed by numbers
            if not total_chapters:
                chapter_match = re.search(r'Số chương\s*:\s*(\d+)', response.text)
                if chapter_match:
                    total_chapters = int(chapter_match.group(1))

            if not total_chapters:
                raise ValueError("Không tìm thấy số chương trong trang")

            print(f"✓ Tổng số chương: {total_chapters}")

            # Calculate max pages
            max_pages = math.ceil(total_chapters / CHAPTERS_PER_PAGE)

            return {
                'base_url': base_url,
                'novel_slug': novel_slug,
                'novel_id': novel_id,
                'novel_title': novel_title,
                'novel_author': novel_author,
                'novel_description': novel_description,
                'cover_image': cover_image,
                'max_pages': max_pages,
                'total_chapters': total_chapters
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Lỗi khi tải trang: {e}")
        except Exception as e:
            raise Exception(f"Lỗi khi phân tích trang: {e}")

    def get_chapter_list(self, novel_info, delay=0.5):
        """
        Fetch list of all chapters

        Args:
            novel_info: Dict containing novel information from parse_novel_url
            delay: Delay time between requests (seconds)

        Returns:
            List of dicts containing chapter information
        """
        chapters = []
        page = 1
        base_url = novel_info['base_url']
        novel_id = novel_info['novel_id']
        max_pages = novel_info.get('max_pages')

        if max_pages:
            print(f"\nĐang lấy danh sách chương ({max_pages} trang)...")
        else:
            print("\nĐang lấy danh sách chương...")

        while True:
            # Check if reached max pages
            if max_pages and page > max_pages:
                print(f"(Đã đạt giới hạn {max_pages} trang)")
                break
            try:
                url = f"{base_url}/get/listchap/{novel_id}?page={page}"
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
                    if not href or 'javascript:' in href:
                        continue

                    # Check if href contains 'chuong-' pattern
                    if '/chuong-' not in href.lower():
                        continue

                    chapter_info = {
                        'title': link.get_text(strip=True),
                        'url': urljoin(base_url, href),
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
        response = self.session.get(chapter_url, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find div containing content - in order of priority
        content_div = soup.find('div', class_='truyen') or \
                     soup.find('div', id='chapter-content') or \
                     soup.find('div', class_='chapter-content') or \
                     soup.find('div', id='content')

        if not content_div:
            raise ValueError("Không tìm thấy nội dung chương")

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
