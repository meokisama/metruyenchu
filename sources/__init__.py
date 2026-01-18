#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sources package - Registry for all novel sources
"""

from sources.metruyenchu_com_vn import MetruyenchuComVnSource
from sources.metruyenhot_me import MetruyenhotMeSource

# Registry of all available sources
SOURCES = {
    '1': {
        'name': 'metruyenchu.com.vn',
        'class': MetruyenchuComVnSource,
        'description': 'Mê Truyện Chữ'
    },
    '2': {
        'name': 'metruyenhot.me',
        'class': MetruyenhotMeSource,
        'description': 'Mê Truyện Hot'
    }
}


def get_source_by_key(key):
    """Get source class by registry key"""
    if key in SOURCES:
        return SOURCES[key]['class']
    return None


def print_sources():
    """Print available sources for user selection"""
    print("\nChọn nguồn truyện:")
    for key, source in SOURCES.items():
        print(f"  {key}. {source['name']} - {source['description']}")
