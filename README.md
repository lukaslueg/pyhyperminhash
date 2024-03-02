# Hyperminhash for Python

[![Docs](https://docs.rs/hyperminhash/badge.svg)](https://docs.rs/hyperminhash)
[![PyPI](https://badge.fury.io/py/pyhyperminhash.svg)](https://pypi.org/project/pyhyperminhash/)

Very fast, constant memory-footprint cardinality approximation, including intersection
and union operation.

The class `Sketch` can be used to count unique elements that were encountered during
the instance's lifetime. Unlike e.g. when using a `set`, the memory consumed by the
`Sketch`-instance does _not_ grow as elements are added; each `Sketch`-instance
consumes approximately 32kb of memory, independent of the number of elements.

Adding new elements to a `Sketch` is preferably done using `.add_bytes()`, akin
to `.digest()` for `hashlib`-objects. It is also possible to use `.add()` if a bytes-like
object can't be provided; the object's `hash()` is then used to provide a unique
identifier for that object.

```python
# Construct an empty Sketch
sk = pyhyperminhash.Sketch()
assert not bool(sk)  # The Sketch is empty
sk.add_bytes(b'Foo')  # Add elements
sk.add_bytes(b'Bar')
sk.add(42)
assert bool(sk)  # The Sketch is not empty
assert float(sk) == sk.cardinality()  # Approximately 3.0
assert int(sk) == len(sk)  # Approximately 3

sk2 = pyhyperminhash.Sketch()
sk2.add_bytes(b'Foobar')
sk2 &= sk1  # sk2 now holds all elements that were in `sk` or `sk2`

sk3 = pyhyperminhash.Sketch()
sk3.add(42)
sk3.add_bytes(b'Foo')
assert sk3.intersection(sk1) > 0.0  # Approximately 1.0, due to `Foo`

buf = sk.save()  # Serialize the Sketch into a bytes-buffer
new_sk = pyhyperminhash.Sketch.load(buf)  # Deserialize a Sketch
assert len(new_sk) == len(sk)

# Construct a Sketch from any iterator directly.
# This is faster than adding elements one by one.
sk = pyhyperminhash.Sketch.from_iter(iter(range(100)))

with open('complaints.txt', 'rb') as f:
    sk = pyhyperminhash.Sketch.from_iter_bytes(f)
```

Although convenient, using `.add()` over `.add_bytes()` has two downsides:

* It may be slower, as the object's own `hash()` may have to be computed
* The Python interpreter probably randomizes hash-values at interpreter-startup,
in order to prevent certain DOS-attacks. The randomness introduced here means that
the count-approximation provided by this package may not be stable from run to run.

See the documentation for the underlying [implementation](https://docs.rs/hyperminhash) for additional information.

### Usage as a sqlite3 aggregate function

```python
class PyHyperminhashCounter:
    def __init__(self):
        self.sk = pyhyperminhash.Sketch()

    def step(self, *args) -> None:
        self.sk += args

    def finalize(self) -> int:
        return int(self.sk)


con = sqlite3.connect(":memory:")
# Create the function for the current connection
con.create_aggregate("pyhmh", -1, PyHyperminhashCounter)

# Some dummy data
cur = con.execute("CREATE TABLE test(i, j)")
cur.executemany("INSERT INTO test(i, j) VALUES(?, ?)",
                ((f'foo{i % 4291}bar', i % 819)
                 for i in range(1000000)))

# Returns exactly 502047
cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT i, j FROM test)")
print(cur.fetchone()[0])

# Returns approximately 500000, but faster
cur.execute("SELECT pyhmh(i, j) FROM test")
print(cur.fetchone()[0])
```

### Performance examples

Reading a file of 55 million lines, 725.940 unique elements, 100 characters per line on average.

Method                     | Wall-clock time | Memory consumed | Count   |
---------------------------|-----------------|-----------------|---------|
_no work_                  | 9.5 seconds     | _nil_           | _nil_   |
`Sketch.from_iter_bytes()` | 10.13 seconds   | ~32 kilobytes   | 734,628 |
`set()`                    | 14.99 seconds   | ~164 megabytes  | 725,940 |

### FAQ

* Can I extract an element that was previously added from a `Sketch`?
  * No.
* Can I check if an element has previously been added to a `Sketch`?
  * No.
* Wow, why use this, then?
  * It's very fast at counting unique things. And it does not use much memory.
