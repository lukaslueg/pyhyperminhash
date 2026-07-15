from __future__ import annotations

import io
import time

import pyhyperminhash

try:
    import pyperf
except ImportError as exc:  # pragma: no cover - exercised manually
    raise SystemExit(
        "Install pyperf in the active environment first: pip install pyperf"
    ) from exc


def build_sketch(start: int, stop: int) -> pyhyperminhash.Sketch:
    return pyhyperminhash.Sketch.from_iter(iter(range(start, stop)))


class Fixtures:
    def __init__(self) -> None:
        self.add_object_values = tuple(f"foo{i}" for i in range(1024))
        self.add_bytes_values = tuple(
            i.to_bytes(2, "little") * 2048 for i in range(256)
        )
        self.from_iter_payload = tuple(f"foo{i}".encode() for i in range(10_000))

        self.reader_payload = b"x" * (256 * 1024)
        self.reader_chunks = tuple(
            self.reader_payload[idx : idx + 4096]
            for idx in range(0, len(self.reader_payload), 4096)
        )

        self.compare_left = build_sketch(0, 200_000)
        self.compare_right = build_sketch(100_000, 300_000)

        self.batch_left = build_sketch(0, 200_000)
        self.batch_others = tuple(
            build_sketch(offset * 25_000, offset * 25_000 + 200_000)
            for offset in range(12)
        )
        self.large_batch_left = build_sketch(0, 50_000)
        self.large_batch_others = tuple(
            build_sketch(offset * 250, offset * 250 + 50_000) for offset in range(1000)
        )


FIXTURES = Fixtures()


def time_add_values(
    loops: int,
    values: tuple[str, ...] | tuple[bytes, ...],
    method: str,
) -> float:
    sketch = pyhyperminhash.Sketch()
    add = getattr(sketch, method)
    t0 = time.perf_counter()
    for _ in range(loops):
        for value in values:
            add(value)
    return time.perf_counter() - t0


def time_from_iter(loops: int, payload: tuple[bytes, ...]) -> float:
    t0 = time.perf_counter()
    for _ in range(loops):
        pyhyperminhash.Sketch.from_iter(iter(payload))
    return time.perf_counter() - t0


def time_add_reader(loops: int, payload: bytes) -> float:
    sketch = pyhyperminhash.Sketch()
    t0 = time.perf_counter()
    for _ in range(loops):
        sketch.add_reader(io.BytesIO(payload))
    return time.perf_counter() - t0


def time_entry_reader(loops: int, chunks: tuple[bytes, ...]) -> float:
    sketch = pyhyperminhash.Sketch()
    t0 = time.perf_counter()
    for _ in range(loops):
        entry = pyhyperminhash.Entry()
        for chunk in chunks:
            entry.add(chunk)
        sketch.add_entry(entry)
    return time.perf_counter() - t0


def time_pair_method(
    loops: int,
    left: pyhyperminhash.Sketch,
    right: pyhyperminhash.Sketch,
    method: str,
    fast: bool,
    batch_size: int,
) -> float:
    compare = getattr(left, method)
    t0 = time.perf_counter()
    for _ in range(loops):
        for _ in range(batch_size):
            compare(right, fast=fast)
    return time.perf_counter() - t0


def time_many_method(
    loops: int,
    left: pyhyperminhash.Sketch,
    others: tuple[pyhyperminhash.Sketch, ...],
    method: str,
    batch_size: int,
) -> float:
    compare = getattr(left, method)
    t0 = time.perf_counter()
    for _ in range(loops):
        for _ in range(batch_size):
            compare(others)
    return time.perf_counter() - t0


def time_many_loop(
    loops: int,
    left: pyhyperminhash.Sketch,
    others: tuple[pyhyperminhash.Sketch, ...],
    method: str,
    fast: bool,
    batch_size: int,
) -> float:
    compare = getattr(left, method)
    t0 = time.perf_counter()
    for _ in range(loops):
        for _ in range(batch_size):
            for other in others:
                compare(other, fast=fast)
    return time.perf_counter() - t0


def register_benchmarks(runner: pyperf.Runner) -> None:
    runner.metadata["pyhyperminhash_version"] = pyhyperminhash.__version__
    runner.metadata["hyperminhash_version"] = pyhyperminhash.__hyperminhash_version__
    runner.metadata["profile"] = pyhyperminhash.__profile__
    runner.metadata["suite_style"] = "local chunked workloads"

    runner.bench_time_func(
        "Sketch.add object batch (1024 objects)",
        time_add_values,
        FIXTURES.add_object_values,
        "add",
        inner_loops=len(FIXTURES.add_object_values),
    )
    runner.bench_time_func(
        "Sketch.add(bytes) batch (256 x 4KiB)",
        time_add_values,
        FIXTURES.add_bytes_values,
        "add",
        inner_loops=len(FIXTURES.add_bytes_values),
    )
    runner.bench_time_func(
        "Sketch.add_bytes(bytes) batch (256 x 4KiB)",
        time_add_values,
        FIXTURES.add_bytes_values,
        "add_bytes",
        inner_loops=len(FIXTURES.add_bytes_values),
    )
    runner.bench_time_func(
        "Sketch.from_iter (10k bytes input)",
        time_from_iter,
        FIXTURES.from_iter_payload,
    )
    runner.bench_time_func(
        "Sketch.add_reader (256KiB)",
        time_add_reader,
        FIXTURES.reader_payload,
    )
    runner.bench_time_func(
        "Entry.add + Sketch.add_entry (256KiB)",
        time_entry_reader,
        FIXTURES.reader_chunks,
    )

    runner.bench_time_func(
        "Sketch.intersection (prepared pair)",
        time_pair_method,
        FIXTURES.compare_left,
        FIXTURES.compare_right,
        "intersection",
        False,
        1,
    )
    runner.bench_time_func(
        "Sketch.intersection (prepared pair, fast=True, x64)",
        time_pair_method,
        FIXTURES.compare_left,
        FIXTURES.compare_right,
        "intersection",
        True,
        64,
        inner_loops=64,
    )
    runner.bench_time_func(
        "Sketch.similarity (prepared pair)",
        time_pair_method,
        FIXTURES.compare_left,
        FIXTURES.compare_right,
        "similarity",
        False,
        1,
    )
    runner.bench_time_func(
        "Sketch.similarity (prepared pair, fast=True, x256)",
        time_pair_method,
        FIXTURES.compare_left,
        FIXTURES.compare_right,
        "similarity",
        True,
        256,
        inner_loops=256,
    )

    runner.bench_time_func(
        f"Sketch.similarity_many ({len(FIXTURES.batch_others)} sketches)",
        time_many_method,
        FIXTURES.batch_left,
        FIXTURES.batch_others,
        "similarity_many",
        1,
    )
    runner.bench_time_func(
        f"Sketch.similarity loop ({len(FIXTURES.batch_others)} sketches)",
        time_many_loop,
        FIXTURES.batch_left,
        FIXTURES.batch_others,
        "similarity",
        False,
        1,
    )
    runner.bench_time_func(
        f"Sketch.similarity_many ({len(FIXTURES.large_batch_others)} sketches)",
        time_many_method,
        FIXTURES.large_batch_left,
        FIXTURES.large_batch_others,
        "similarity_many",
        1,
    )
    runner.bench_time_func(
        f"Sketch.similarity loop ({len(FIXTURES.large_batch_others)} sketches)",
        time_many_loop,
        FIXTURES.large_batch_left,
        FIXTURES.large_batch_others,
        "similarity",
        False,
        1,
    )
    runner.bench_time_func(
        f"Sketch.similarity loop ({len(FIXTURES.large_batch_others)} sketches, fast=True)",
        time_many_loop,
        FIXTURES.large_batch_left,
        FIXTURES.large_batch_others,
        "similarity",
        True,
        1,
    )


def main() -> None:
    runner = pyperf.Runner(processes=6, values=4, min_time=0.05)
    runner.parse_args()
    register_benchmarks(runner)


if __name__ == "__main__":
    main()
