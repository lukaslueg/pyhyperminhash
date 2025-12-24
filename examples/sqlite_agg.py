import sqlite3

import pyhyperminhash
import simple


class PyHyperminhashCounter:
    def __init__(self):
        self.sk = pyhyperminhash.Sketch()

    def step(self, *args) -> None:
        self.sk += args

    def finalize(self) -> int:
        return int(self.sk)


con = sqlite3.connect(":memory:")
con.create_aggregate("pyhmh", -1, PyHyperminhashCounter)

# Some dummy data
cur = con.execute("CREATE TABLE test(i, j)")
cur.executemany(
    "INSERT INTO test(i, j) VALUES(?, ?)",
    ((f"foo{i % 4291}bar", i % 819) for i in range(10_000_000)),
)

# Returns exactly 502047
with simple.timeit() as t:
    cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT i, j FROM test)")
    ln = cur.fetchone()[0]
print(f"DISTINCT: {ln}, {t():.4f} secs")

# Returns approximately 500000, but faster
with simple.timeit() as t:
    cur.execute("SELECT pyhmh(i, j) FROM test")
    ln = cur.fetchone()[0]
print(f"Sketch: {ln}, {t():.4f} secs")
