"""
MemoryManager - 三维记忆管理器

核心功能:
- Factual Memory (事实记忆)
- Experiential Memory (经验记忆)
- Working Memory (工作记忆)

本地化优势:
- 文件读写本地处理
- 记忆解析本地完成
- Token消耗降低90%+
"""

from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class MemoryManager:
    """
    三维记忆管理器

    使用方式:
        memory = MemoryManager('Docs/MEMORY.md')

        # 设置事实记忆
        memory.set_factual('project.name', 'QuickAgents')
        memory.set_factual('project.tech_stack', ['Python', 'TypeScript'])

        # 添加经验记忆
        memory.add_experiential('踩坑', 'Windows换行符问题')

        # 更新工作记忆
        memory.set_working('current_task', '实现FileManager')

        # 获取记忆
        name = memory.get('project.name')

        # 保存
        memory.save()
    """

    def __init__(self, memory_path: str = "Docs/MEMORY.md"):
        """
        初始化记忆管理器

        Args:
            memory_path: 记忆文件路径
        """
        self.memory_path = Path(memory_path)
        self.factual: Dict[str, Any] = {}
        self.experiential: List[Dict] = []
        self.working: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> bool:
        """
        加载记忆文件

        Returns:
            是否成功加载
        """
        if not self.memory_path.exists():
            return False

        try:
            content = self.memory_path.read_text(encoding="utf-8")
            self._parse(content)
            self._loaded = True
            return True
        except Exception as e:
            print(f"加载记忆失败: {e}")
            return False

    def save(self) -> bool:
        """
        保存记忆文件

        Returns:
            是否成功保存
        """
        try:
            # 确保目录存在
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)

            content = self._generate()
            self.memory_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            print(f"保存记忆失败: {e}")
            return False

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取记忆值

        Args:
            key: 键名（支持点分隔，如 'project.name'）
            default: 默认值

        Returns:
            记忆值
        """
        if not self._loaded:
            self.load()

        # 先查工作记忆，再查事实记忆
        for source in [self.working, self.factual]:
            value = self._get_nested(source, key)
            if value is not None:
                return value

        return default

    def set_factual(self, key: str, value: Any) -> None:
        """设置事实记忆"""
        if not self._loaded:
            self.load()
        self._set_nested(self.factual, key, value)

    def set_working(self, key: str, value: Any) -> None:
        """设置工作记忆"""
        if not self._loaded:
            self.load()
        self._set_nested(self.working, key, value)

    def add_experiential(
        self, category: str, content: str, tags: Optional[List[str]] = None
    ) -> None:
        """添加经验记忆"""
        if not self._loaded:
            self.load()

        entry = {
            "category": category,
            "content": content,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.experiential.append(entry)

    def search(self, keyword: str) -> List[Dict]:
        """
        搜索记忆

        Args:
            keyword: 关键词

        Returns:
            匹配的记忆列表
        """
        if not self._loaded:
            self.load()

        results = []

        # 搜索事实记忆
        for key, value in self._flatten(self.factual).items():
            if key is not None and value is not None:
                key_str = str(key)
                value_str = str(value)
                if (
                    keyword.lower() in key_str.lower()
                    or keyword.lower() in value_str.lower()
                ):
                    results.append({"type": "factual", "key": key, "value": value})

        # 搜索经验记忆
        for entry in self.experiential:
            if entry and isinstance(entry, dict):
                content = entry.get("content", "")
                if content and keyword.lower() in content.lower():
                    results.append({"type": "experiential", **entry})

        return results

    def clear_working(self) -> None:
        """清空工作记忆"""
        self.working = {}

    def _parse(self, content: str) -> None:
        """解析记忆文件"""
        # 简单解析逻辑
        lines = content.split("\n")
        current_section = None

        for line in lines:
            if "## Factual Memory" in line:
                current_section = "factual"
            elif "## Experiential Memory" in line:
                current_section = "experiential"
            elif "## Working Memory" in line:
                current_section = "working"
            elif line.strip().startswith("- ") and current_section:
                # 解析列表项
                item = line.strip()[2:]
                if ":" in item:
                    key, value = item.split(":", 1)
                    # 移除markdown粗体标记
                    key = key.strip().replace("**", "")
                    value = value.strip()
                    if current_section == "factual":
                        # 使用 _set_nested 重建嵌套结构
                        self._set_nested(self.factual, key, value)
                    elif current_section == "working":
                        # 使用 _set_nested 重建嵌套结构
                        self._set_nested(self.working, key, value)
                    elif current_section == "experiential":
                        self.experiential.append({"content": item})

    def _generate(self) -> str:
        """生成记忆文件内容"""
        lines = [
            "# MEMORY.md",
            "",
            f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
            "## Factual Memory (事实记忆)",
            "",
        ]

        for key, value in self._flatten(self.factual).items():
            lines.append(f"- {key}: {value}")

        lines.extend(["", "## Experiential Memory (经验记忆)", ""])

        for entry in self.experiential[-20:]:  # 最近20条
            lines.append(f"- {entry.get('category', '')}: {entry.get('content', '')}")

        lines.extend(["", "## Working Memory (工作记忆)", ""])

        for key, value in self._flatten(self.working).items():
            lines.append(f"- {key}: {value}")

        lines.append("")
        return "\n".join(lines)

    def _get_nested(self, data: Dict, key: str) -> Any:
        """获取嵌套值"""
        keys = key.split(".")
        value = data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        return value

    def _set_nested(self, data: Dict, key: str, value: Any) -> None:
        """设置嵌套值"""
        keys = key.split(".")
        current = data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def _flatten(self, data: Dict, prefix: str = "") -> Dict:
        """扁平化字典"""
        result = {}
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten(value, new_key))
            else:
                result[new_key] = value
        return result
