import sys
import os
import string

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import generate_share_code

def test_generate_share_code_length():
    code = generate_share_code()
    assert len(code) == 6

def test_generate_share_code_charset():
    code = generate_share_code()
    valid_chars = set(string.ascii_uppercase + string.digits)
    assert all(c in valid_chars for c in code)

def test_generate_share_code_randomness():
    # Generate 100 codes and ensure they are all unique
    codes = {generate_share_code() for _ in range(100)}
    assert len(codes) == 100
