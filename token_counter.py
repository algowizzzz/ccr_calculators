#!/usr/bin/env python3
"""
Estimate token count for JSON files using different methods.
"""

import json
import sys
from pathlib import Path

def estimate_tokens_simple(text):
    """Simple token estimation: ~4 characters per token on average"""
    return len(text) / 4

def estimate_tokens_word_based(text):
    """Word-based token estimation: ~0.75 tokens per word"""
    words = len(text.split())
    return words * 0.75

def estimate_tokens_advanced(text):
    """More advanced estimation considering JSON structure"""
    # JSON has more punctuation and structure, so slightly higher ratio
    # Typical JSON: ~3.5 characters per token
    return len(text) / 3.5

def analyze_file(file_path):
    """Analyze a file and provide token estimates"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Basic stats
        char_count = len(content)
        word_count = len(content.split())
        line_count = content.count('\n') + 1
        
        # Token estimates
        simple_tokens = estimate_tokens_simple(content)
        word_tokens = estimate_tokens_word_based(content)
        advanced_tokens = estimate_tokens_advanced(content)
        
        # Try to parse as JSON for additional info
        try:
            json_data = json.loads(content)
            is_valid_json = True
        except:
            is_valid_json = False
        
        print(f"File: {file_path}")
        print(f"=" * 50)
        print(f"Character count: {char_count:,}")
        print(f"Word count: {word_count:,}")
        print(f"Line count: {line_count:,}")
        print(f"Valid JSON: {is_valid_json}")
        print()
        print("Token Estimates:")
        print(f"  Simple (÷4):     ~{simple_tokens:,.0f} tokens")
        print(f"  Word-based (×0.75): ~{word_tokens:,.0f} tokens")
        print(f"  Advanced (÷3.5):   ~{advanced_tokens:,.0f} tokens")
        print()
        print(f"Average estimate: ~{(simple_tokens + word_tokens + advanced_tokens) / 3:,.0f} tokens")
        
        # Size categories
        if advanced_tokens < 1000:
            size_category = "Small"
        elif advanced_tokens < 4000:
            size_category = "Medium"
        elif advanced_tokens < 8000:
            size_category = "Large"
        elif advanced_tokens < 16000:
            size_category = "Very Large"
        else:
            size_category = "Extremely Large"
        
        print(f"Size category: {size_category}")
        
        return {
            'chars': char_count,
            'words': word_count,
            'lines': line_count,
            'tokens_estimate': int(advanced_tokens),
            'size_category': size_category
        }
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python token_counter.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    analyze_file(file_path)

