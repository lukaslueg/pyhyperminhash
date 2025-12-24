# Hyperminhash for Python

[![Docs](https://docs.rs/hyperminhash/badge.svg)](https://docs.rs/hyperminhash)
[![PyPI](https://badge.fury.io/py/pyhyperminhash.svg)](https://pypi.org/project/pyhyperminhash/)

Very fast, constant memory-footprint cardinality approximation, including intersection
and union operation.

The class `Sketch` can be used to count unique elements that were encountered during
the instance's lifetime. Unlike e.g. when using a `set`, the memory consumed by the
`Sketch`-instance does _not_ grow as elements are added; each `Sketch`-instance
consumes approximately 32kb of memory, independent of the number of elements.

```python
# Basic usage

# Construct an empty Sketch
sk = pyhyperminhash.Sketch()
assert not sk  # The Sketch is empty
sk.add('Foo')  # Add elements
sk.add('Bar')
sk.add(42)
assert sk  # The Sketch is not empty
assert float(sk) == sk.cardinality()  # Approximately 3.0
assert int(sk) == len(sk)  # Approximately 3
```

```python
# Sketches can be combined...

sk2 = pyhyperminhash.Sketch()
sk2.add('Foobar')
sk2 &= sk  # sk2 now holds all elements that were in `sk` or `sk2`

sk3 = pyhyperminhash.Sketch()
sk3.add(42)
sk3.add('Foo')
assert sk3.intersection(sk1) > 0.0  # Approximately 1.0, due to `Foo`
```

```python
# Sketches can be stored for later use

buf = sk.save()  # Serialize the Sketch into a bytes-buffer
new_sk = pyhyperminhash.Sketch.load(buf)  # Deserialize a Sketch
assert len(new_sk) == len(sk)
```

```python
# Sketches can be constructed from iterators directly, which avoids
# materializing all objects simultaneously.

# This is also faster than adding elements one by one.
sk = pyhyperminhash.Sketch.from_iter(iter(range(100)))

# Read all lines; uses binary mode to avoid Unicode encoding+decoding
with open('complaints.txt', 'rb') as f:
    sk = pyhyperminhash.Sketch.from_iter(f)

# Add an entire file-like object
with open('complaints.txt', 'rb') as f:
    sk.add_reader(f)
```

```python
# Entry-objects can be used to construct what represents a single
# object from multiple parts. They consume very little memory.

# Add sub-objects that don't fit into memory
e = pyhyperminhash.Entry()
with open('complaints.txt', 'rb') as f:
    e.add(f.read(4096))  # Add two parts to this Entry
    e.add(f.read(4096))
    sk.add_entry(e)  # This counts as one object

sk1.add_entry(e)  # Entry-objects can be added to mulitple Sketches

# Entry-objects can be "forked" at the state they are currently at
e2 = e.fork()
e2.add("Foo")
sk.add_entry(e2)  # This is a new object in `Sketch`...

e3 = e.fork()
e3.add("Bar")
sk.add_entry(e3)  # So is this, without re-computing `e`
```

It is very much preferred to provide `bytes` to `Sketch.add()` and `Entry.add()`,
in order to avoid double-hashing the content. Also, notice that the Python interpreter
probably randomizes hash-values at interpreter-startup (in order to prevent certain kinds
of DOS-attacks). The randomness introduced here means that the count-approximation provided
by this package may not be stable from run to run.

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

Reading a file of 50 million lines, ~1,000,000 unique elements, 20 characters per line.

Method                     | Wall-clock time | Memory consumed | Count      |
---------------------------|-----------------|-----------------|------------|
Count lines                | 2.3 seconds     | _nil_           | 50,000,000 |
`set()`                    | 14.99 seconds   | ~144 megabytes  | 1,048,576  |
`Sketch.from_iter()`       | 1.8 seconds     | ~32 kilobytes   | 1,041,936  |

### FAQ

* Can I extract an element that was previously added from a `Sketch`?
  * No.
* Can I check if an element has previously been added to a `Sketch`?
  * No.
* Wow, why use this, then?
  * It's very fast at counting unique things. And it does not use much memory.
