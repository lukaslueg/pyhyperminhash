import typing


class Sketch:
    @staticmethod
    def load(buf: bytes) -> 'Sketch':
        ...

    @staticmethod
    def from_iter(iter: typing.Iterator) -> 'Sketch':
        ...

    @staticmethod
    def from_iter_bytes(iter: typing.Iterator[bytes]) -> 'Sketch':
        ...

    def save(self) -> bytes:
        ...

    def add(self, obj) -> None:
        ...

    def add_bytes(self, buf: bytes) -> None:
        ...

    def cardinality(self) -> float:
        ...

    def union(self, other: 'Sketch') -> None:
        ...

    def intersection(self, other: 'Sketch') -> float:
        ...

    def __bool__(self) -> bool:
        ...

    def __int__(self) -> int:
        ...

    def __len__(self) -> int:
        ...

    def __float__(self) -> float:
        ...

    def __iand__(self, other: 'Sketch') -> 'Sketch':
        ...

    def __and__(self, other: 'Sketch') -> 'Sketch':
        ...


def __version_info__() -> str:
    ...


__version__: str
__hyperminhash_version__: str
__profile__: str
