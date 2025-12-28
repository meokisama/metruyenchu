#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import math
import html
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from config import DEFAULT_HEADERS, DEFAULT_TIMEOUT


def parse_novel_url(url):
    """
    Parse novel URL to extract all novel information

    Args:
        url: Full URL of the novel page (e.g., https://metruyenchu.com.vn/nuong-tu-dung-la-nu-ma-dau)

    Returns:
        dict: {
            'base_url': str,
            'novel_slug': str,
            'novel_id': int,
            'novel_title': str,
            'novel_author': str,
            'novel_description': str,
            'cover_image': bytes or None,
            'max_pages': int,
            'total_chapters': int
        }
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
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
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
                cover_response = session.get(cover_url, timeout=DEFAULT_TIMEOUT)
                cover_response.raise_for_status()
                cover_image = cover_response.content
                print("✓")
            except Exception as e:
                print(f"✗ ({e})")

        # Extract total chapters
        # Find: <li><b>Số chương :</b> 1179</li>
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

        # Calculate max pages (100 chapters per page)
        max_pages = math.ceil(total_chapters / 100)
        print(f"✓ Số trang cần fetch: {max_pages}")

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
