import random
import typing

import pyhyperminhash
import simple

DEMO_FILE = "demo_file.txt"


def create_file():
    chars = ["a", "b"]
    with open(DEMO_FILE, "xt") as f:
        print("Creating file...")
        for _ in range(50_000_000):
            f.write("".join(random.choices(chars, k=20)))
            f.write("\n")


def read_blank() -> int:
    with open(DEMO_FILE, "rb") as f:
        i = sum(1 for _ in f)
    return i


def read_set() -> int:
    with open(DEMO_FILE, "rb") as f:
        s = set(f)
    return len(s)


def read_phmh() -> int:
    with open(DEMO_FILE, "rb") as f:
        s = pyhyperminhash.Sketch.from_iter_bytes(f)
    return len(s)


def t(name: str, f: typing.Callable[[], int]):
    with simple.timeit() as t:
        ln = f()
    print(f"{name}: {ln}, {t():.4f} secs")


if __name__ == "__main__":
    try:
        create_file()
    except FileExistsError:
        pass
    t("No work", read_blank)
    t("Set", read_set)
    t("Sketch", read_phmh)
