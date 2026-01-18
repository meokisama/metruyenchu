#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base class for all novel sources
"""

from abc import ABC, abstractmethod

from config import DEFAULT_MAX_RETRIES, DEFAULT_DELAY_BETWEEN_REQUESTS


class BaseNovelSource(ABC):
    """Abstract base class for novel sources"""

    # Source identification
    name = "base"
    base_url = ""

    @abstractmethod
    def parse_novel_url(self, url):
        """
        Parse novel URL to extract all novel information

        Args:
            url: Full URL of the novel page

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
        pass

    @abstractmethod
    def get_chapter_list(self, novel_info, delay=0.5):
        """
        Fetch list of all chapters

        Args:
            novel_info: Dict containing novel information from parse_novel_url
            delay: Delay time between requests (seconds)

        Returns:
            List of dicts containing chapter information
        """
        pass

    @abstractmethod
    def get_chapter_content(self, chapter_url):
        """
        Fetch content of a chapter

        Args:
            chapter_url: URL of the chapter

        Returns:
            String containing chapter content (HTML)
        """
        pass

    def crawl_all_chapters(self, chapters, delay=None, max_retries=None):
        """
        Crawl content of all chapters

        Args:
            chapters: List of chapters
            delay: Delay time between requests
            max_retries: Number of retries on error

        Returns:
            List of dicts containing chapter information and content
        """
        import time

        if delay is None:
            delay = DEFAULT_DELAY_BETWEEN_REQUESTS
        if max_retries is None:
            max_retries = DEFAULT_MAX_RETRIES

        print(f"\nDang crawl noi dung {len(chapters)} chuong...")

        for idx, chapter in enumerate(chapters, 1):
            retries = 0
            success = False

            while retries < max_retries and not success:
                try:
                    if retries == 0:
                        print(f"  [{idx}/{len(chapters)}] {chapter['title']}...", end=' ')

                    content = self.get_chapter_content(chapter['url'])
                    chapter['content'] = content

                    print("+")
                    success = True
                    time.sleep(delay)

                except Exception as e:
                    retries += 1
                    error_msg = str(e)
                    if retries < max_retries:
                        print(f"x ({error_msg}) - Thu lai {retries}/{max_retries}...", end=' ')
                        time.sleep(delay * 2)
                    else:
                        print(f"x Bo qua ({error_msg})")
                        chapter['content'] = f"<p>Loi khi tai chuong sau {max_retries} lan thu: {error_msg}</p>"

        return chapters
