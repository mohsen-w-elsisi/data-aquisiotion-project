from typing import TypeVar

_T = TypeVar('_T')


class ReadOnceList[_T]:
    def __init__(self):
        self._list: list[_T] = []
        self._wasRead = False

    def push(self, item: _T) -> None:
        self._list.append(item)

    def read(self):
        self._wasRead = True
        return self._list
