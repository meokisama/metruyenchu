#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
from ebooklib import epub
from config import EPUB_CSS_STYLE


class EpubCreator:
    """Class for creating EPUB files from novel data"""

    def __init__(self, novel_title, novel_author, novel_id,
                 novel_description=None, cover_image=None):
        """
        Initialize EPUB creator

        Args:
            novel_title: Title of the novel
            novel_author: Author of the novel
            novel_id: ID of the novel
            novel_description: Description of the novel (optional)
            cover_image: Cover image as bytes (optional)
        """
        self.novel_title = novel_title
        self.novel_author = novel_author
        self.novel_id = novel_id
        self.novel_description = novel_description
        self.cover_image = cover_image

    def create_epub(self, chapters, output_filename=None):
        """
        Create EPUB file from chapter list

        Args:
            chapters: List of chapters with content
            output_filename: Output filename (optional)

        Returns:
            Path to created EPUB file
        """
        if not output_filename:
            # Create filename from novel title
            safe_title = re.sub(r'[^\w\s-]', '', self.novel_title)
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            output_filename = f"{safe_title}.epub"

        print(f"\nĐang tạo file EPUB: {output_filename}")

        # Create book
        book = epub.EpubBook()

        # Metadata
        book.set_identifier(f'novel_{self.novel_id}_{int(time.time())}')
        book.set_title(self.novel_title)
        book.set_language('vi')
        book.add_author(self.novel_author)

        if self.novel_description:
            book.add_metadata('DC', 'description', self.novel_description)

        # Add cover image if available
        if self.cover_image:
            book.set_cover('cover.jpg', self.cover_image)

        # CSS style
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=EPUB_CSS_STYLE
        )
        book.add_item(nav_css)

        # Create chapters
        epub_chapters = []
        spine = ['nav']

        for idx, chapter in enumerate(chapters, 1):
            # Create chapter
            epub_chapter = epub.EpubHtml(
                title=chapter['title'],
                file_name=f'chapter_{idx}.xhtml',
                lang='vi'
            )

            # Chapter content
            chapter_content = f'''
            <h1>{chapter['title']}</h1>
            {chapter['content']}
            '''

            epub_chapter.set_content(chapter_content)
            epub_chapter.add_item(nav_css)

            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
            spine.append(epub_chapter)

        # Add navigation
        book.toc = tuple(epub_chapters)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Spine
        book.spine = spine

        # Write file
        epub.write_epub(output_filename, book)

        file_size = os.path.getsize(output_filename) / (1024 * 1024)
        print(f"✓ Đã tạo file EPUB: {output_filename} ({file_size:.2f} MB)")

        return output_filename
