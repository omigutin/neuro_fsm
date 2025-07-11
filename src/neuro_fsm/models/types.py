__all__ = [
    'StateKeyType',
    'CountersDict',
]

from typing import TypeAlias, Union

StateKeyType: TypeAlias = Union[str, int]
CountersDict: TypeAlias = dict[int, int]

