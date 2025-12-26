import io
import typing

import pyhyperminhash

import simple


def print_res(name: str, t: float, r: int, b: int | None = None) -> None:
    if b is None:
        print(f"{name}: {t:.1f} secs, {(r / t) / 1000:.1f} Kop/s")
    else:
        print(
            f"{name}: {t:.1f} secs, {(r / t) / 1000:.1f} Kop/s, {(b / t) / 1024**2:.1f} Mb/s"
        )


def bench(
    name: str, r: int, f: typing.Callable, init: typing.Callable | None = None
) -> None:
    b = 0
    with simple.timeit() as t:
        for _ in range(r):
            if init is not None:
                b += f(init()) or 0
            else:
                b += f() or 0
    print_res(name, t(), r, b or None)


def bench_cardinality():
    sk = pyhyperminhash.Sketch()

    def inner():
        sk.cardinality()

    bench("Sketch.cardinality", 500_000, inner)


def bench_add():
    sk = pyhyperminhash.Sketch()
    bench("Sketch.add object", 10_000_000, lambda: sk.add("Foobar"))


def bench_bytes():
    sk = pyhyperminhash.Sketch()
    for obj, name, r in [
        (b"x", "Sketch.add,   1 byte", 10_000_000),
        (b"x" * 10, "Sketch.add,  10 bytes", 10_000_000),
        (b"x" * 100, "Sketch.add, 100 bytes", 10_000_000),
        (b"x" * 1024, "Sketch.add,  1 Kb", 5_000_000),
        (b"x" * 16384, "Sketch.add, 16 Kb", 1_000_000),
        (b"x" * 1024 * 1024, "Sketch.add,  1 Mb", 20_000),
        (b"x" * 10 * 1024 * 1024, "Sketch.add, 10 Mb", 5_000),
    ]:

        def inner():
            sk.add(obj)
            return len(obj)

        bench(name, r, inner)


def bench_entry_add():
    sk = pyhyperminhash.Sketch()

    def inner(r):
        e = pyhyperminhash.Entry()
        i = 0
        while buf := r.read(4096):
            e.add(buf)
            i += len(buf)
        sk.add_entry(e)
        return i

    bench(
        "Entry.add, manual reader",
        10_000,
        inner,
        lambda: io.BytesIO(b"x" * 1024 * 1024),
    )


def bench_reader():
    sk = pyhyperminhash.Sketch()

    def inner(r):
        return sk.add_reader(r)

    bench("Sketch.add_reader", 10_000, inner, lambda: io.BytesIO(b"x" * 1024 * 1024))


def _main():
    bench_cardinality()
    print("---")
    bench_add()
    print("---")
    bench_bytes()
    print("---")
    bench_entry_add()
    print("---")
    bench_reader()


if __name__ == "__main__":
    _main()
