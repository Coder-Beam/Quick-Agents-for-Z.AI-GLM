#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FileManager 综合测试脚本"""

from quickagents.core.file_manager import FileManager
from quickagents.utils.encoding import read_file_utf8, write_file_utf8
import os
import tempfile
import shutil
import time

def test_file_manager():
    """测试 FileManager 核心功能"""
    # 创建测试目录
    test_dir = tempfile.mkdtemp()
    print('=' * 60)
    print('[TEST 1] FileManager Initialization')
    print('=' * 60)
    
    fm = FileManager()
    print('[OK] FileManager initialized')
    
    # Test 2: File Hash
    print()
    print('=' * 60)
    print('[TEST 2] File Hash Test')
    print('=' * 60)
    
    test_file = os.path.join(test_dir, 'test.txt')
    write_file_utf8(test_file, 'Hello, World! This is a test file with emoji 😀')
    print('[OK] Test file created:', test_file)
    
    hash1 = fm.get_file_hash(test_file)
    print('[OK] File hash:', hash1[:16] + '...')
    
    # Same content should produce same hash
    hash2 = fm.get_file_hash(test_file)
    print('[OK] Same file hash:', hash2[:16] + '...')
    assert hash1 == hash2, 'Same file should produce same hash'
    print('[OK] Hash consistency verified')
    
    # Test 3: Read if Changed
    print()
    print('=' * 60)
    print('[TEST 3] Read if Changed Test')
    print('=' * 60)
    
    # First read (should be new)
    content1, changed1 = fm.read_if_changed(test_file)
    print('[OK] First read: changed={}'.format(changed1))
    print('[OK] Content length:', len(content1))
    assert changed1 == True, 'First read should be changed'
    
    # Second read (should use cache)
    content2, changed2 = fm.read_if_changed(test_file)
    print('[OK] Second read: changed={}'.format(changed2))
    assert changed2 == False, 'Second read should use cache'
    assert content1 == content2, 'Cached content should match'
    print('[OK] Cache working correctly')
    
    # Modify file and read again
    time.sleep(0.1)  # Ensure timestamp difference
    write_file_utf8(test_file, 'Modified content! Updated with new emoji 🎉')
    content3, changed3 = fm.read_if_changed(test_file)
    print('[OK] After modification: changed={}'.format(changed3))
    assert changed3 == True, 'Modified file should be detected as changed'
    print('[OK] Change detection working')
    
    # Test 4: Write File
    print()
    print('=' * 60)
    print('[TEST 4] Write File Test')
    print('=' * 60)
    
    write_file = os.path.join(test_dir, 'output.txt')
    fm.write(write_file, 'This is written content with Chinese: 你好世界 and emoji: 🚀')
    print('[OK] File written')
    
    # Verify written content
    written_content = read_file_utf8(write_file)
    assert '你好世界' in written_content, 'Chinese characters should be preserved'
    assert '🚀' in written_content, 'Emoji should be preserved'
    print('[OK] Written content verified')
    
    # Test 5: Edit File
    print()
    print('=' * 60)
    print('[TEST 5] Edit File Test')
    print('=' * 60)
    
    edit_file = os.path.join(test_dir, 'edit_test.txt')
    write_file_utf8(edit_file, 'Line 1: Old content\nLine 2: Keep this\nLine 3: Old content')
    print('[OK] Test file created for editing')
    
    # Successful edit
    result1 = fm.edit(edit_file, 'Old content', 'New content')
    print('[OK] Edit result:', result1['success'])
    assert result1['success'] == True, 'Edit should succeed'
    print('[OK] Lines changed:', result1.get('lines_changed', 0))
    
    # Failed edit (old string not found)
    result2 = fm.edit(edit_file, 'Non-existent string', 'Replacement')
    print('[OK] Failed edit result:', result2['success'])
    assert result2['success'] == False, 'Edit should fail for non-existent string'
    print('[OK] Error message:', result2['message'])
    
    # Test 6: Binary File Handling
    print()
    print('=' * 60)
    print('[TEST 6] Binary File Test')
    print('=' * 60)
    
    binary_file = os.path.join(test_dir, 'binary.bin')
    with open(binary_file, 'wb') as f:
        f.write(b'\x00\x01\x02\x03\xFF\xFE')
    print('[OK] Binary file created')
    
    # Read binary file should work
    binary_content = read_file_utf8(binary_file)
    print('[OK] Binary file read, length:', len(binary_content))
    
    # Test 7: Large File Handling
    print()
    print('=' * 60)
    print('[TEST 7] Large File Test')
    print('=' * 60)
    
    large_file = os.path.join(test_dir, 'large.txt')
    large_content = 'Large file test\n' * 1000  # ~18KB
    write_file_utf8(large_file, large_content)
    print('[OK] Large file created: {} bytes'.format(len(large_content)))
    
    large_read, changed = fm.read_if_changed(large_file)
    print('[OK] Large file read: changed={}, length={}'.format(changed, len(large_read)))
    assert len(large_read) == len(large_content), 'Large file content should match'
    print('[OK] Large file handling verified')
    
    # Test 8: Special Characters
    print()
    print('=' * 60)
    print('[TEST 8] Special Characters Test')
    print('=' * 60)
    
    special_file = os.path.join(test_dir, 'special.txt')
    special_content = '''
Special characters test:
- Chinese: 中文测试 成功
- Japanese: テスト成功
- Korean: 테스트 성공
- Emoji: 😀 🎉 🚀 ✅ 💯
- Symbols: © ® ™ € £ ¥ ₹
- Math: ∑ ∫ √ ∞ ≈ ≠
'''
    write_file_utf8(special_file, special_content)
    print('[OK] Special characters file created')
    
    special_read = read_file_utf8(special_file)
    assert '中文测试' in special_read, 'Chinese should be preserved'
    assert '😀' in special_read, 'Emoji should be preserved'
    assert '∑' in special_read, 'Math symbols should be preserved'
    print('[OK] All special characters preserved')
    
    # Test 9: Nested Directory Creation
    print()
    print('=' * 60)
    print('[TEST 9] Nested Directory Test')
    print('=' * 60)
    
    nested_file = os.path.join(test_dir, 'level1', 'level2', 'level3', 'nested.txt')
    fm.write(nested_file, 'Content in nested directory')
    print('[OK] Nested file written')
    
    assert os.path.exists(nested_file), 'Nested file should exist'
    print('[OK] Nested directories created successfully')
    
    # Cleanup
    shutil.rmtree(test_dir)
    
    print()
    print('=' * 60)
    print('[SUCCESS] FileManager All Core Tests Passed!')
    print('=' * 60)

if __name__ == '__main__':
    test_file_manager()
