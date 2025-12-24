import contextlib
import time
import typing

import pyhyperminhash


@contextlib.contextmanager
def timeit() -> typing.Generator[typing.Callable[[], float], None, None]:
    t1 = t2 = time.perf_counter()
    yield lambda: t2 - t1
    t2 = time.perf_counter()


if __name__ == "__main__":
    inp = [f"foo{i}" for i in range(10_000_000)]

    with timeit() as t:
        ln = len(set(inp))
    print(f"Set: {ln}, {t():.4f} secs")

    with timeit() as t:
        ln = len(pyhyperminhash.Sketch.from_iter(iter(inp)))
    print(f"Sketch: {ln}, {t():.4f} secs")
