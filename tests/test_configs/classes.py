from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class NeuroClass(object):
    cls_id: int
    name: str
    full_name: str = ""
    fiction: bool = False  # True - статус фиктивный(выдуманный)
    threshold: Optional[float] = None


class NeuroClasses(Enum):
    UNDEFINED = NeuroClass(cls_id=-1, name="UNDEFINED", fiction=True, threshold=1)
    EMPTY = NeuroClass(cls_id=0, name="EMPTY", full_name="EMPTY description", fiction=False)
    FULL = NeuroClass(cls_id=1, name="FULL", full_name="FULL description")
    UNKNOWN = NeuroClass(cls_id=2, name="UNKNOWN", threshold=None)

    @property
    def cls_id(self) -> int:
        return self.value.cls_id

    @property
    def name(self) -> str:
        return self.value.name

    @property
    def full_name(self) -> str:
        return self.value.full_name

    @property
    def fiction(self) -> bool:
        return self.value.fiction
