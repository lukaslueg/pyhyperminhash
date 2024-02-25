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
sk = pyhyperminhash.Sketch()
assert not bool(sk)  # The Sketch is empty
sk.add_bytes(b'Foo')
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
```

Although convenient, using `.add()` over `.add_bytes()` has two downsides:

* It may be slower, as the object's own `hash()` may have to be computed
* The Python interpreter probably randomizes hash-values at interpreter-startup,
in order to prevent certain DOS-attacks. The randomness introduced here means that
the count-approximation provided by this package may not be stable from run to run.

See the documentation for the underlying [implementation](https://docs.rs/hyperminhash) for additional information.
