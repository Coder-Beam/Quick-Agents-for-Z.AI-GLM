"""
愚公循环任务编排器

负责 UserStory 的生命周期管理:
- 添加/更新/查询 Story
- 按优先级 + 依赖关系选择下一个 Story
- 跟踪完成进度
"""

from typing import Optional

from .models import (
    UserStory,
    StoryPriority,
    StoryStatus,
    ParsedRequirement,
)


class TaskOrchestrator:
    """
    任务编排器

    核心职责:
    1. 管理 UserStory 集合
    2. 按优先级 + 依赖选择下一个可执行 Story
    3. 提供进度统计
    """

    def __init__(self):
        self._stories: dict[str, UserStory] = {}

    # === Story 管理 ===

    def add_story(self, story: UserStory) -> None:
        """添加一个 Story"""
        self._stories[story.id] = story

    def add_stories(self, stories: list[UserStory]) -> None:
        """批量添加 Stories"""
        for story in stories:
            self.add_story(story)

    def load_from_requirement(self, requirement: ParsedRequirement) -> None:
        """从解析后的需求加载 Stories"""
        self._stories.clear()
        self.add_stories(requirement.user_stories)

    def get_story(self, story_id: str) -> Optional[UserStory]:
        """获取指定 Story"""
        return self._stories.get(story_id)

    def get_all_stories(self) -> list[UserStory]:
        """获取所有 Stories"""
        return list(self._stories.values())

    def update_story(self, story: UserStory) -> None:
        """更新 Story"""
        self._stories[story.id] = story

    def remove_story(self, story_id: str) -> bool:
        """移除 Story, 返回是否成功"""
        if story_id in self._stories:
            del self._stories[story_id]
            return True
        return False

    # === Story 选择 ===

    def get_next_story(self) -> Optional[UserStory]:
        """
        选择下一个可执行的 Story

        选择策略:
        1. 过滤: 仅 PENDING / FAILED(可重试) 状态
        2. 过滤: 依赖已满足(全部 PASSED)
        3. 排序: 优先级升序 (CRITICAL=1 最高)
        4. 排序: 同优先级按 ID 升序 (稳定排序)
        5. 返回第一个
        """
        candidates = []
        for story in self._stories.values():
            if not self._is_executable(story):
                continue
            candidates.append(story)

        if not candidates:
            return None

        # 按优先级升序, 同优先级按 ID 升序
        candidates.sort(key=lambda s: (s.priority.value, s.id))
        return candidates[0]

    def _is_executable(self, story: UserStory) -> bool:
        """判断 Story 是否可执行"""
        # 状态检查: PENDING 或 FAILED(可重试)
        if story.status == StoryStatus.PENDING:
            pass
        elif story.status == StoryStatus.FAILED and story.can_retry():
            pass
        else:
            return False

        # 依赖检查: 所有依赖必须 PASSED
        for dep_id in story.dependencies:
            dep = self._stories.get(dep_id)
            if dep is None or dep.status != StoryStatus.PASSED:
                return False

        return True

    # === 进度统计 ===

    @property
    def total_stories(self) -> int:
        """总 Story 数"""
        return len(self._stories)

    @property
    def completed_stories(self) -> int:
        """已完成的 Story 数 (PASSED)"""
        return sum(1 for s in self._stories.values() if s.status == StoryStatus.PASSED)

    @property
    def failed_stories(self) -> int:
        """失败且不可重试的 Story 数"""
        return sum(1 for s in self._stories.values() if s.status == StoryStatus.FAILED and not s.can_retry())

    @property
    def pending_stories(self) -> int:
        """待执行的 Story 数"""
        return sum(1 for s in self._stories.values() if s.status == StoryStatus.PENDING)

    @property
    def all_done(self) -> bool:
        """是否全部完成 (PASSED 或跳过/取消)"""
        if not self._stories:
            return False
        return all(
            s.status in (StoryStatus.PASSED, StoryStatus.SKIPPED, StoryStatus.CANCELLED) for s in self._stories.values()
        )

    def get_progress(self) -> dict:
        """获取进度统计"""
        total = self.total_stories
        completed = self.completed_stories
        return {
            "total": total,
            "completed": completed,
            "pending": self.pending_stories,
            "failed": self.failed_stories,
            "progress_pct": (completed / total * 100) if total > 0 else 0.0,
        }

    def get_stories_by_status(self, status: StoryStatus) -> list[UserStory]:
        """按状态筛选 Stories"""
        return [s for s in self._stories.values() if s.status == status]

    def get_stories_by_priority(self, priority: StoryPriority) -> list[UserStory]:
        """按优先级筛选 Stories"""
        return [s for s in self._stories.values() if s.priority == priority]

    def get_blocked_stories(self) -> list[UserStory]:
        """获取被阻塞的 Stories"""
        blocked = []
        for story in self._stories.values():
            if story.status == StoryStatus.PENDING and story.is_blocked_by(self._stories):
                blocked.append(story)
        return blocked

    # === 序列化 ===

    def to_list(self) -> list[dict]:
        """导出为字典列表"""
        return [s.to_dict() for s in self._stories.values()]

    def from_list(self, data: list[dict]) -> None:
        """从字典列表导入"""
        self._stories.clear()
        for item in data:
            story = UserStory.from_dict(item)
            self._stories[story.id] = story
