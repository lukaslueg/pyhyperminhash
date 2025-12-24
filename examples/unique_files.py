import itertools
import os
import sys
import typing

import pyhyperminhash


def walk(path: str) -> typing.Iterator[str]:
    for path, _, files in os.walk(path):
        for file in files:
            yield os.path.join(path, file)


def count_unique_files(path: str) -> pyhyperminhash.Sketch:
    sk = pyhyperminhash.Sketch()
    bytecount = filecount = 0
    for fname in walk(path):
        with open(fname, "rb") as f:
            bytecount += sk.add_reader(f)
            filecount += 1
    print(f"`{path}`: {filecount} files, {len(sk)} unique files, {bytecount} bytes")
    return sk


if __name__ == "__main__":
    sketches: list[tuple[str, pyhyperminhash.Sketch]] = []
    for path in sys.argv[1:]:
        sketches.append((path, count_unique_files(path)))
    if sketches:
        print("---")
    if len(sketches) > 1:
        for (p1, s1), (p2, s2) in itertools.combinations(sketches, 2):
            if p1 == p2:
                continue
            print(
                f"`{p1}`, `{p2}`: approx. {int(s1.intersection(s2))} files are the same ({s1.similarity(s2) * 100:.1f}%)"
            )
