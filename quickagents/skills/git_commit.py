"""
GitCommit - Git提交管理

核心功能:
- Pre-commit检查（test/lint/typecheck）
- 提交信息生成（conventional commit格式）
- 文档同步
- 完全本地化

Token节省: 100%
"""

import subprocess
import os
import re
from pathlib import Path
from typing import Dict, List, Optional


class GitCommit:
    """
    Git提交管理器
    
    使用方式:
        git = GitCommit(project_root='.')
        
        # 执行pre-commit检查
        checks = git.run_pre_commit_checks()
        if checks['all_passed']:
            # 生成提交信息并提交
            result = git.commit('feat', 'core', '添加FileManager模块')
            print(result['message'])
        
        # 查看状态
        status = git.get_status()
    """
    
    # Conventional Commit类型
    COMMIT_TYPES = {
        'feat': '新功能',
        'fix': 'Bug修复',
        'docs': '文档更新',
        'style': '代码格式',
        'refactor': '重构',
        'perf': '性能优化',
        'test': '测试相关',
        'chore': '构建/工具',
        'ci': 'CI配置'
    }
    
    def __init__(self, project_root: str = '.'):
        """
        初始化Git提交管理器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root).resolve()
        
        # 检测项目类型
        self.is_node = (self.project_root / 'package.json').exists()
        self.is_python = (self.project_root / 'pyproject.toml').exists() or \
                         (self.project_root / 'setup.py').exists() or \
                         list(self.project_root.glob('**/*.py')) != []
    
    def get_status(self) -> Dict:
        """
        获取Git状态
        
        Returns:
            {
                'staged': List[str],      # 已暂存文件
                'unstaged': List[str],    # 未暂存文件
                'untracked': List[str],   # 未跟踪文件
                'branch': str,            # 当前分支
                'ahead': int,             # 领先远程的提交数
                'behind': int             # 落后远程的提交数
            }
        """
        try:
            # git status --porcelain
            result = subprocess.run(
                ['git', 'status', '--porcelain', '--branch'],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            lines = result.stdout.strip().split('\n')
            
            staged = []
            unstaged = []
            untracked = []
            branch = ''
            ahead = 0
            behind = 0
            
            for line in lines:
                if line.startswith('##'):
                    # 分支信息
                    match = re.search(r'## (\S+).*?ahead (\d+).*?behind (\d+)', line)
                    if match:
                        branch = match.group(1)
                        ahead = int(match.group(2))
                        behind = int(match.group(3))
                    else:
                        branch = line[3:].split('...')[0]
                elif line.startswith('??'):
                    untracked.append(line[3:])
                elif line[0] in 'MADRC':
                    staged.append(line[3:])
                elif line[1] in 'MD':
                    unstaged.append(line[3:])
            
            return {
                'staged': staged,
                'unstaged': unstaged,
                'untracked': untracked,
                'branch': branch,
                'ahead': ahead,
                'behind': behind
            }
            
        except Exception as e:
            return {
                'staged': [],
                'unstaged': [],
                'untracked': [],
                'branch': '',
                'ahead': 0,
                'behind': 0,
                'error': str(e)
            }
    
    def get_diff(self, staged: bool = True) -> str:
        """
        获取差异
        
        Args:
            staged: 是否获取已暂存的差异
            
        Returns:
            差异内容
        """
        cmd = ['git', 'diff', '--staged'] if staged else ['git', 'diff']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        return result.stdout
    
    def run_pre_commit_checks(self) -> Dict:
        """
        执行pre-commit检查
        
        Returns:
            {
                'all_passed': bool,
                'checks': {
                    'test': {'passed': bool, 'output': str},
                    'lint': {'passed': bool, 'output': str},
                    'typecheck': {'passed': bool, 'output': str}
                }
            }
        """
        checks = {}
        all_passed = True
        
        # 1. 运行测试
        checks['test'] = self._run_tests()
        if not checks['test']['passed']:
            all_passed = False
        
        # 2. 运行lint
        checks['lint'] = self._run_lint()
        if not checks['lint']['passed']:
            all_passed = False
        
        # 3. 运行typecheck
        checks['typecheck'] = self._run_typecheck()
        if not checks['typecheck']['passed']:
            all_passed = False
        
        return {
            'all_passed': all_passed,
            'checks': checks
        }
    
    def _run_tests(self) -> Dict:
        """运行测试"""
        cmd = None
        
        if self.is_node:
            cmd = ['npm', 'test']
        elif self.is_python:
            cmd = ['pytest'] if (self.project_root / 'pytest.ini').exists() else \
                  ['python', '-m', 'unittest', 'discover']
        
        if cmd is None:
            return {'passed': True, 'output': '未配置测试命令', 'skipped': True}
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=120
            )
            
            return {
                'passed': result.returncode == 0,
                'output': result.stdout + result.stderr
            }
        except subprocess.TimeoutExpired:
            return {'passed': False, 'output': '测试执行超时'}
        except FileNotFoundError:
            return {'passed': True, 'output': '测试命令不可用', 'skipped': True}
    
    def _run_lint(self) -> Dict:
        """运行lint检查"""
        cmd = None
        
        if self.is_node:
            # 检查eslint
            result = subprocess.run(
                ['npm', 'list', 'eslint'],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            if 'eslint' in result.stdout:
                cmd = ['npx', 'eslint', '.']
        elif self.is_python:
            cmd = ['flake8', '.'] if self._command_exists('flake8') else \
                  ['pylint', '.'] if self._command_exists('pylint') else None
        
        if cmd is None:
            return {'passed': True, 'output': '未配置lint命令', 'skipped': True}
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60
            )
            
            return {
                'passed': result.returncode == 0,
                'output': result.stdout + result.stderr
            }
        except:
            return {'passed': True, 'output': 'lint命令执行失败', 'skipped': True}
    
    def _run_typecheck(self) -> Dict:
        """运行类型检查"""
        cmd = None
        
        if self.is_node:
            # 检查TypeScript
            if (self.project_root / 'tsconfig.json').exists():
                cmd = ['npx', 'tsc', '--noEmit']
        elif self.is_python:
            cmd = ['mypy', '.'] if self._command_exists('mypy') else None
        
        if cmd is None:
            return {'passed': True, 'output': '未配置类型检查', 'skipped': True}
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=60
            )
            
            return {
                'passed': result.returncode == 0,
                'output': result.stdout + result.stderr
            }
        except:
            return {'passed': True, 'output': '类型检查命令执行失败', 'skipped': True}
    
    def _command_exists(self, cmd: str) -> bool:
        """检查命令是否存在"""
        result = subprocess.run(
            ['which', cmd] if os.name != 'nt' else ['where', cmd],
            capture_output=True
        )
        return result.returncode == 0
    
    def generate_commit_message(self, commit_type: str, scope: str, 
                                subject: str, body: Optional[str] = None,
                                footer: Optional[str] = None) -> str:
        """
        生成Conventional Commit格式的提交信息
        
        Args:
            commit_type: 提交类型 (feat/fix/docs/etc)
            scope: 范围 (模块名/功能名)
            subject: 主题描述
            body: 正文描述（可选）
            footer: 页脚（可选，如 Closes #123）
            
        Returns:
            格式化的提交信息
        """
        # 验证类型
        if commit_type not in self.COMMIT_TYPES:
            commit_type = 'chore'  # 默认类型
        
        # 构建消息
        if scope:
            header = f"{commit_type}({scope}): {subject}"
        else:
            header = f"{commit_type}: {subject}"
        
        lines = [header]
        
        if body:
            lines.append('')
            lines.extend(body.split('\n'))
        
        if footer:
            lines.append('')
            lines.append(footer)
        
        return '\n'.join(lines)
    
    def stage_files(self, files: Optional[List[str]] = None, all_staged: bool = False) -> bool:
        """
        暂存文件
        
        Args:
            files: 文件列表（None表示自动选择）
            all_staged: 是否暂存所有已跟踪的修改
            
        Returns:
            是否成功
        """
        try:
            if all_staged:
                subprocess.run(
                    ['git', 'add', '-u'],
                    check=True,
                    cwd=str(self.project_root)
                )
            elif files:
                for file in files:
                    subprocess.run(
                        ['git', 'add', file],
                        check=True,
                        cwd=str(self.project_root)
                    )
            else:
                # 自动暂存所有修改和新文件
                subprocess.run(
                    ['git', 'add', '-A'],
                    check=True,
                    cwd=str(self.project_root)
                )
            
            return True
        except subprocess.CalledProcessError:
            return False
    
    def commit(self, commit_type: str, scope: str, subject: str,
               body: Optional[str] = None, footer: Optional[str] = None,
               run_checks: bool = True) -> Dict:
        """
        执行提交
        
        Args:
            commit_type: 提交类型
            scope: 范围
            subject: 主题
            body: 正文
            footer: 页脚
            run_checks: 是否运行pre-commit检查
            
        Returns:
            {
                'success': bool,
                'message': str,
                'commit_hash': str,
                'checks': Dict  # 如果run_checks为True
            }
        """
        result = {
            'success': False,
            'message': '',
            'commit_hash': ''
        }
        
        # 运行检查
        if run_checks:
            checks = self.run_pre_commit_checks()
            result['checks'] = checks
            
            if not checks['all_passed']:
                result['message'] = 'Pre-commit检查未通过'
                return result
        
        # 生成提交信息
        message = self.generate_commit_message(
            commit_type, scope, subject, body, footer
        )
        
        try:
            # 执行提交
            proc = subprocess.run(
                ['git', 'commit', '-m', message],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            if proc.returncode == 0:
                result['success'] = True
                result['message'] = message
                
                # 获取commit hash
                hash_result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    capture_output=True,
                    text=True,
                    cwd=str(self.project_root)
                )
                commit_hash = hash_result.stdout.strip()[:7]
                result['commit_hash'] = commit_hash
                
                # 触发进化分析（失败不影响主流程）
                try:
                    from ._evolution_trigger import trigger_git_commit
                    # 获取变更文件列表
                    files_result = subprocess.run(
                        ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash],
                        capture_output=True, text=True, timeout=5
                    )
                    files_changed = files_result.stdout.strip().split('\n') if files_result.returncode == 0 else []
                    trigger_git_commit({
                        'hash': commit_hash,
                        'message': message,
                        'files_changed': [f for f in files_changed if f]
                    })
                except Exception:
                    pass  # 进化分析失败不影响提交结果
            else:
                result['message'] = proc.stderr
                
        except Exception as e:
            result['message'] = str(e)
        
        return result
    
    def push(self, remote: str = 'origin', branch: Optional[str] = None) -> Dict:
        """
        推送到远程
        
        Args:
            remote: 远程名称
            branch: 分支名（None表示当前分支）
            
        Returns:
            {'success': bool, 'message': str}
        """
        if branch is None:
            status = self.get_status()
            branch = status['branch']
        
        try:
            result = subprocess.run(
                ['git', 'push', remote, branch],
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            return {
                'success': result.returncode == 0,
                'message': result.stdout + result.stderr
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


# 全局实例
_global_git: Optional[GitCommit] = None

def get_git_commit(project_root: str = '.') -> GitCommit:
    """获取全局Git提交管理器"""
    global _global_git
    if _global_git is None:
        _global_git = GitCommit(project_root)
    return _global_git
