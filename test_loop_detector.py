"""
LoopDetector 测试脚本

测试范围:
1. 基本循环检测
2. 阈值触发
3. 窗口大小限制
4. 重置功能
5. 统计信息
6. should_pause 方法
7. 全局实例
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from quickagents.core.loop_detector import LoopDetector, get_loop_detector
from quickagents.core.cache_db import CacheDB


class TestLoopDetector:
    """LoopDetector 测试类"""
    
    def __init__(self):
        self.test_dir = None
        self.passed = 0
        self.failed = 0
        self.results = []
        self.test_count = 0
    
    def setup(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp(prefix='loop_test_')
        self.passed = 0
        self.failed = 0
        self.results = []
        self.test_count = 0
        print(f"\n{'='*60}")
        print("LoopDetector 测试开始")
        print(f"{'='*60}")
        print(f"测试目录: {self.test_dir}\n")
    
    def teardown(self):
        """测试后清理"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        print(f"\n{'='*60}")
        print(f"测试完成: {self.passed} 通过, {self.failed} 失败")
        print(f"{'='*60}\n")
    
    def get_fresh_db_path(self):
        """获取新的数据库路径（每个测试独立）"""
        self.test_count += 1
        return os.path.join(self.test_dir, f'test_{self.test_count}.db')
    
    def log(self, name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((name, passed, message))
        if passed:
            self.passed += 1
            print(f"  {status} - {name}")
        else:
            self.failed += 1
            print(f"  {status} - {name}: {message}")
    
    # ==================== 测试用例 ====================
    
    def test_init(self):
        """测试1: 初始化"""
        try:
            detector = LoopDetector(threshold=3, window_size=20, db_path=self.get_fresh_db_path())
            
            assert detector.threshold == 3, "阈值设置错误"
            assert detector.window_size == 20, "窗口大小设置错误"
            assert detector.db is not None, "数据库未初始化"
            assert detector._history == [], "历史记录应初始化为空"
            
            self.log("初始化", True)
        except Exception as e:
            self.log("初始化", False, str(e))
    
    def test_no_loop_initial(self):
        """测试2: 初次调用不触发循环"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            
            result = detector.check('read', {'path': 'test.md'})
            
            assert result is None, "初次调用不应触发循环"
            assert len(detector._history) == 1, "历史记录应有1条"
            
            self.log("初次调用不触发循环", True)
        except Exception as e:
            self.log("初次调用不触发循环", False, str(e))
    
    def test_threshold_trigger(self):
        """测试3: 阈值触发"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            tool_args = {'path': 'test.md'}
            
            # 第1次调用
            r1 = detector.check('read', tool_args)
            assert r1 is None, "第1次不应触发"
            
            # 第2次调用
            r2 = detector.check('read', tool_args)
            assert r2 is None, "第2次不应触发"
            
            # 第3次调用 - 应该触发
            r3 = detector.check('read', tool_args)
            assert r3 is not None, "第3次应触发"
            assert r3['detected'] == True, "detected应为True"
            assert r3['tool_name'] == 'read', "tool_name应为read"
            assert r3['count'] == 3, "count应为3"
            
            self.log("阈值触发", True)
        except Exception as e:
            self.log("阈值触发", False, str(e))
    
    def test_different_args_no_loop(self):
        """测试4: 不同参数不触发循环"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            
            # 不同参数
            for i in range(5):
                result = detector.check('read', {'path': f'file{i}.md'})
            
            patterns = detector.get_loop_patterns()
            assert len(patterns) == 0, "不同参数不应产生循环模式"
            
            self.log("不同参数不触发循环", True)
        except Exception as e:
            self.log("不同参数不触发循环", False, str(e))
    
    def test_window_size(self):
        """测试5: 窗口大小限制"""
        try:
            detector = LoopDetector(threshold=10, window_size=5, db_path=self.get_fresh_db_path())
            
            # 调用超过窗口大小
            for i in range(10):
                detector.check('read', {'path': f'file{i}.md'})
            
            # 窗口应只保留最后5条
            assert len(detector._history) == 5, f"窗口应为5，实际为{len(detector._history)}"
            
            self.log("窗口大小限制", True)
        except Exception as e:
            self.log("窗口大小限制", False, str(e))
    
    def test_window_count(self):
        """测试6: 窗口内计数"""
        try:
            detector = LoopDetector(threshold=3, window_size=10, db_path=self.get_fresh_db_path())
            tool_args = {'path': 'test.md'}
            
            # 调用4次（触发阈值后继续）
            for i in range(4):
                result = detector.check('read', tool_args)
            
            # 第4次应包含窗口计数
            assert result is not None, "应触发循环"
            assert 'window_count' in result, "应包含window_count"
            assert result['window_count'] == 4, f"窗口计数应为4，实际为{result['window_count']}"
            
            self.log("窗口内计数", True)
        except Exception as e:
            self.log("窗口内计数", False, str(e))
    
    def test_reset(self):
        """测试7: 重置功能"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            tool_args = {'path': 'test.md'}
            
            # 触发循环
            for i in range(3):
                detector.check('read', tool_args)
            
            patterns_before = detector.get_loop_patterns()
            assert len(patterns_before) > 0, "重置前应有循环模式"
            
            # 重置
            detector.reset()
            
            # 验证历史清空
            assert detector._history == [], "历史应清空"
            
            # 验证数据库清空
            patterns_after = detector.get_loop_patterns()
            assert len(patterns_after) == 0, "重置后应无循环模式"
            
            self.log("重置功能", True)
        except Exception as e:
            self.log("重置功能", False, str(e))
    
    def test_stats(self):
        """测试8: 统计信息"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            tool_args = {'path': 'test.md'}
            
            # 触发循环
            for i in range(3):
                detector.check('read', tool_args)
            
            stats = detector.get_stats()
            
            assert 'total_patterns' in stats, "应包含total_patterns"
            assert 'threshold' in stats, "应包含threshold"
            assert 'window_size' in stats, "应包含window_size"
            assert 'current_window_count' in stats, "应包含current_window_count"
            assert stats['total_patterns'] >= 1, "应有循环模式"
            assert stats['threshold'] == 3, "阈值应为3"
            assert stats['window_size'] == 20, "窗口大小应为20"
            
            self.log("统计信息", True)
        except Exception as e:
            self.log("统计信息", False, str(e))
    
    def test_should_pause(self):
        """测试9: should_pause 方法"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            tool_args = {'path': 'test.md'}
            
            # 前2次不暂停
            for i in range(2):
                pause = detector.should_pause('read', tool_args)
                assert pause == False, f"第{i+1}次不应暂停"
            
            # 第3次应暂停
            pause = detector.should_pause('read', tool_args)
            assert pause == True, "第3次应暂停"
            
            self.log("should_pause 方法", True)
        except Exception as e:
            self.log("should_pause 方法", False, str(e))
    
    def test_global_instance(self):
        """测试10: 全局实例"""
        try:
            # 获取全局实例
            detector1 = get_loop_detector(threshold=5)
            detector2 = get_loop_detector(threshold=10)  # 第二次参数应被忽略
            
            # 应该是同一个实例
            assert detector1 is detector2, "应返回同一个全局实例"
            assert detector1.threshold == 5, "阈值应为首次设置的5"
            
            self.log("全局实例", True)
        except Exception as e:
            self.log("全局实例", False, str(e))
    
    def test_multiple_tools(self):
        """测试11: 多工具独立检测"""
        try:
            detector = LoopDetector(threshold=3, db_path=self.get_fresh_db_path())
            
            # read 工具调用2次（不触发）
            for i in range(2):
                detector.check('read', {'path': 'test.md'})
            
            # write 工具调用2次（不触发）
            write_result = None
            for i in range(2):
                write_result = detector.check('write', {'path': 'test.md'})
            
            # write 不应触发（只有2次）
            assert write_result is None, f"write不应触发，但返回了: {write_result}"
            
            # read 再调用1次（触发）
            read_result = detector.check('read', {'path': 'test.md'})
            assert read_result is not None, "read应触发（共3次）"
            
            self.log("多工具独立检测", True)
        except Exception as e:
            self.log("多工具独立检测", False, str(e))
    
    def test_persistence(self):
        """测试12: 数据持久化"""
        try:
            db_path = self.get_fresh_db_path()
            # 第一个检测器
            detector1 = LoopDetector(threshold=3, db_path=db_path)
            for i in range(3):
                detector1.check('read', {'path': 'test.md'})
            
            patterns1 = detector1.get_loop_patterns()
            
            # 创建第二个检测器（相同数据库）
            detector2 = LoopDetector(threshold=3, db_path=db_path)
            patterns2 = detector2.get_loop_patterns()
            
            # 应该读取到相同的数据
            assert len(patterns1) == len(patterns2), "持久化数据应一致"
            
            self.log("数据持久化", True)
        except Exception as e:
            self.log("数据持久化", False, str(e))
    
    def run(self):
        """运行所有测试"""
        self.setup()
        
        try:
            self.test_init()
            self.test_no_loop_initial()
            self.test_threshold_trigger()
            self.test_different_args_no_loop()
            self.test_window_size()
            self.test_window_count()
            self.test_reset()
            self.test_stats()
            self.test_should_pause()
            self.test_global_instance()
            self.test_multiple_tools()
            self.test_persistence()
        finally:
            self.teardown()
        
        return self.failed == 0


if __name__ == '__main__':
    tester = TestLoopDetector()
    success = tester.run()
    sys.exit(0 if success else 1)
