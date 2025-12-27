#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Default headers for HTTP requests
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Request settings
DEFAULT_DELAY_BETWEEN_REQUESTS = 1.0
DEFAULT_CHAPTER_LIST_DELAY = 0.5
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# EPUB CSS Style
EPUB_CSS_STYLE = '''
@namespace epub "http://www.idpf.org/2007/ops";
body {
    font-family: Georgia, "Times New Roman", Times, serif;
    line-height: 1.8;
    margin: 2em;
}
h1 {
    text-align: center;
    margin-bottom: 1em;
    color: #333;
}
p {
    text-align: justify;
    margin: 0.5em 0;
    text-indent: 2em;
}
'''
