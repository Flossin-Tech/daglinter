# -*- coding: utf-8 -*-
"""Test file with Unicode content."""

# Various Unicode characters
# 日本語コメント
# Émojis and symbols: 🚀 🎉 ✨ ⚡ 🔥
# Math symbols: ∑ ∫ ∂ √ ∞
# Currency: € £ ¥ ₹
# Other: café naïve résumé

from airflow import DAG

dag = DAG(
    'unicode_test',
    doc_md='''
    # Unicode DAG Documentation 🚀

    This DAG contains Unicode: 日本語
    Special chars: café, naïve
    Symbols: ∑∫∂√∞
    '''
)

def process_unicode():
    """Process Unicode data."""
    message = "Hello 世界 🌍"
    data = {
        'greeting': 'Bonjour',
        'emoji': '🎉',
        'math': '∑i=1→n'
    }
    return data
