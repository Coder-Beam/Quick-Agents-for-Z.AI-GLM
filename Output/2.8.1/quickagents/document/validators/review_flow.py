"""
User review confirmation flow.

Provides a structured interface for users to review, accept,
reject, or modify analysis results from each pipeline layer.
"""

import logging
from typing import List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ReviewItem:
    """Single reviewable item."""

    def __init__(
        self,
        item_id: str,
        item_type: str,
        content: str,
        source: str = "",
        confidence: float = 0.0,
    ):
        self.item_id = item_id
        self.item_type = item_type
        self.content = content
        self.source = source
        self.confidence = confidence
        self.status = ReviewStatus.PENDING
        self.user_note: Optional[str] = None

    def accept(self, note: Optional[str] = None) -> None:
        self.status = ReviewStatus.ACCEPTED
        self.user_note = note

    def reject(self, note: Optional[str] = None) -> None:
        self.status = ReviewStatus.REJECTED
        self.user_note = note

    def modify(self, new_content: str, note: Optional[str] = None) -> None:
        self.status = ReviewStatus.MODIFIED
        self.content = new_content
        self.user_note = note

    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "content": self.content,
            "source": self.source,
            "confidence": self.confidence,
            "status": self.status.value,
            "user_note": self.user_note,
        }


class ReviewSession:
    """Manages a review session for pipeline results."""

    def __init__(self):
        self._items: Dict[str, ReviewItem] = {}
        self._phase: str = "init"

    def add_item(
        self,
        item_id: str,
        item_type: str,
        content: str,
        source: str = "",
        confidence: float = 0.0,
    ) -> ReviewItem:
        item = ReviewItem(item_id, item_type, content, source, confidence)
        self._items[item_id] = item
        return item

    def get_item(self, item_id: str) -> Optional[ReviewItem]:
        return self._items.get(item_id)

    def get_pending(self) -> List[ReviewItem]:
        return [
            item for item in self._items.values()
            if item.status == ReviewStatus.PENDING
        ]

    def get_by_status(self, status: ReviewStatus) -> List[ReviewItem]:
        return [
            item for item in self._items.values()
            if item.status == status
        ]

    def accept_all(self, note: Optional[str] = None) -> int:
        count = 0
        for item in self._items.values():
            if item.status == ReviewStatus.PENDING:
                item.accept(note)
                count += 1
        return count

    def reject_all(self, note: Optional[str] = None) -> int:
        count = 0
        for item in self._items.values():
            if item.status == ReviewStatus.PENDING:
                item.reject(note)
                count += 1
        return count

    def accept_auto(self, min_confidence: float = 0.9) -> int:
        """Auto-accept items above confidence threshold."""
        count = 0
        for item in self._items.values():
            if item.status == ReviewStatus.PENDING and item.confidence >= min_confidence:
                item.accept("Auto-accepted (high confidence)")
                count += 1
        return count

    @property
    def phase(self) -> str:
        return self._phase

    @phase.setter
    def phase(self, value: str) -> None:
        self._phase = value

    def summary(self) -> Dict:
        total = len(self._items)
        by_status: Dict[str, int] = {}
        for item in self._items.values():
            by_status[item.status.value] = by_status.get(item.status.value, 0) + 1
        return {
            "phase": self._phase,
            "total": total,
            "by_status": by_status,
            "pending": by_status.get("pending", 0),
        }

    def is_complete(self) -> bool:
        return all(
            item.status != ReviewStatus.PENDING
            for item in self._items.values()
        )

    def get_results(self) -> Dict:
        accepted = [i for i in self._items.values() if i.status == ReviewStatus.ACCEPTED]
        modified = [i for i in self._items.values() if i.status == ReviewStatus.MODIFIED]
        rejected = [i for i in self._items.values() if i.status == ReviewStatus.REJECTED]
        return {
            "accepted": [i.to_dict() for i in accepted],
            "modified": [i.to_dict() for i in modified],
            "rejected": [i.to_dict() for i in rejected],
        }
