"""
TDDWorkflow - TDD工作流管理

核心功能:
- RED阶段: 运行测试，验证失败
- GREEN阶段: 运行测试，验证通过
- REFACTOR阶段: 确保测试仍通过
- 完全本地化

Token节省: 100%
"""

import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class TDDPhase(Enum):
    """TDD阶段"""
    RED = 'red'
    GREEN = 'green'
    REFACTOR = 'refactor'
    COMPLETE = 'complete'


class TDDWorkflow:
    """
    TDD工作流管理器
    
    使用方式:
        tdd = TDDWorkflow(project_root='.')
        
        # RED阶段：运行测试（应该失败）
        result = tdd.run_red('test_user_login.py')
        if result['passed']:
            print("警告：测试已通过，需要先写失败的测试")
        
        # GREEN阶段：运行测试（应该通过）
        result = tdd.run_green('test_user_login.py')
        if result['passed']:
            print("测试通过，可以进入Refactor")
        
        # REFACTOR阶段：确保测试仍通过
        result = tdd.run_refactor('test_user_login.py')
        
        # 获取统计
        stats = tdd.get_stats()
    """
    
    def __init__(self, project_root: str = '.', 
                 test_command: str = None,
                 state_file: str = '.quickagents/tdd_state.json'):
        """
        初始化TDD工作流
        
        Args:
            project_root: 项目根目录
            test_command: 测试命令（自动检测）
            state_file: 状态文件路径
        """
        self.project_root = Path(project_root).resolve()
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 自动检测测试命令
        if test_command:
            self.test_command = test_command
        else:
            self.test_command = self._detect_test_command()
        
        # 加载状态
        self.state = self._load_state()
    
    def _detect_test_command(self) -> str:
        """检测项目的测试命令"""
        # 检查package.json
        pkg_json = self.project_root / 'package.json'
        if pkg_json.exists():
            import json
            with open(pkg_json) as f:
                pkg = json.load(f)
                scripts = pkg.get('scripts', {})
                if 'test' in scripts:
                    return 'npm test'
                elif 'pytest' in scripts:
                    return 'pytest'
        
        # 检查pytest
        if (self.project_root / 'pytest.ini').exists() or \
           list(self.project_root.glob('**/test_*.py')):
            return 'pytest'
        
        # 检查Python unittest
        if list(self.project_root.glob('**/test_*.py')):
            return 'python -m unittest discover'
        
        # 默认
        return 'npm test'
    
    def run_red(self, test_file: str = None) -> Dict:
        """
        RED阶段：运行测试，验证失败
        
        Args:
            test_file: 特定测试文件（可选）
            
        Returns:
            {
                'passed': bool,        # 测试是否通过（RED阶段应该False）
                'output': str,         # 测试输出
                'duration_ms': int,    # 执行时间
                'phase': str           # 当前阶段
            }
        """
        return self._run_tests(test_file, TDDPhase.RED)
    
    def run_green(self, test_file: str = None) -> Dict:
        """
        GREEN阶段：运行测试，验证通过
        
        Args:
            test_file: 特定测试文件（可选）
            
        Returns:
            同run_red
        """
        return self._run_tests(test_file, TDDPhase.GREEN)
    
    def run_refactor(self, test_file: str = None) -> Dict:
        """
        REFACTOR阶段：确保测试仍通过
        
        Args:
            test_file: 特定测试文件（可选）
            
        Returns:
            同run_red
        """
        return self._run_tests(test_file, TDDPhase.REFACTOR)
    
    def _run_tests(self, test_file: str, phase: TDDPhase) -> Dict:
        """运行测试"""
        start_time = datetime.now()
        
        # 构建命令
        cmd = self.test_command
        if test_file:
            if 'pytest' in cmd:
                cmd = f"{cmd} {test_file}"
            elif 'npm' in cmd:
                cmd = f"{cmd} -- {test_file}"
        
        # 执行测试
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60
            )
            
            output = result.stdout + result.stderr
            passed = result.returncode == 0
            
        except subprocess.TimeoutExpired:
            output = "测试执行超时"
            passed = False
        except Exception as e:
            output = str(e)
            passed = False
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # 记录状态
        self._record_phase(phase, passed, test_file)
        
        return {
            'passed': passed,
            'output': output,
            'duration_ms': duration_ms,
            'phase': phase.value,
            'test_file': test_file
        }
    
    def check_coverage(self, threshold: int = 80) -> Dict:
        """
        检查测试覆盖率
        
        Args:
            threshold: 覆盖率阈值
            
        Returns:
            {
                'coverage': float,     # 覆盖率百分比
                'meets_threshold': bool,
                'report': str          # 覆盖率报告
            }
        """
        # 尝试运行覆盖率命令
        coverage_cmds = [
            'npm run test:coverage',
            'pytest --cov --cov-report=term-missing',
            'coverage report'
        ]
        
        for cmd in coverage_cmds:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root),
                    timeout=120
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    
                    # 解析覆盖率
                    coverage = self._parse_coverage(output)
                    
                    return {
                        'coverage': coverage,
                        'meets_threshold': coverage >= threshold,
                        'report': output
                    }
            except:
                continue
        
        return {
            'coverage': 0,
            'meets_threshold': False,
            'report': '无法获取覆盖率信息'
        }
    
    def _parse_coverage(self, output: str) -> float:
        """解析覆盖率输出"""
        # pytest-cov格式
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if match:
            return float(match.group(1))
        
        # jest/nyc格式
        match = re.search(r'All files[^\d]*(\d+\.?\d*)', output)
        if match:
            return float(match.group(1))
        
        # 通用格式
        match = re.search(r'(\d+\.?\d*)%', output)
        if match:
            return float(match.group(1))
        
        return 0
    
    def get_stats(self) -> Dict:
        """获取TDD统计"""
        return {
            'total_cycles': self.state.get('total_cycles', 0),
            'red_count': self.state.get('red_count', 0),
            'green_count': self.state.get('green_count', 0),
            'refactor_count': self.state.get('refactor_count', 0),
            'last_phase': self.state.get('last_phase'),
            'last_test_file': self.state.get('last_test_file'),
            'test_command': self.test_command
        }
    
    def reset(self) -> None:
        """重置状态"""
        self.state = {
            'total_cycles': 0,
            'red_count': 0,
            'green_count': 0,
            'refactor_count': 0,
            'last_phase': None,
            'last_test_file': None,
            'history': []
        }
        self._save_state()
    
    def _record_phase(self, phase: TDDPhase, passed: bool, test_file: str) -> None:
        """记录阶段状态"""
        self.state['last_phase'] = phase.value
        self.state['last_test_file'] = test_file
        
        if phase == TDDPhase.RED:
            self.state['red_count'] = self.state.get('red_count', 0) + 1
        elif phase == TDDPhase.GREEN:
            self.state['green_count'] = self.state.get('green_count', 0) + 1
        elif phase == TDDPhase.REFACTOR:
            self.state['refactor_count'] = self.state.get('refactor_count', 0) + 1
        
        # 记录历史
        history = self.state.get('history', [])
        history.append({
            'phase': phase.value,
            'passed': passed,
            'test_file': test_file,
            'timestamp': datetime.now().isoformat()
        })
        self.state['history'] = history[-100:]  # 保留最近100条
        
        self._save_state()
    
    def _load_state(self) -> Dict:
        """加载状态"""
        if self.state_file.exists():
            import json
            with open(self.state_file) as f:
                return json.load(f)
        return {
            'total_cycles': 0,
            'red_count': 0,
            'green_count': 0,
            'refactor_count': 0,
            'last_phase': None,
            'last_test_file': None,
            'history': []
        }
    
    def _save_state(self) -> None:
        """保存状态"""
        import json
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)


# 全局实例
_global_tdd: Optional[TDDWorkflow] = None

def get_tdd_workflow(project_root: str = '.') -> TDDWorkflow:
    """获取全局TDD工作流"""
    global _global_tdd
    if _global_tdd is None:
        _global_tdd = TDDWorkflow(project_root)
    return _global_tdd
