import io
import pytest

import pyhyperminhash


def approx(expected: float):
    return pytest.approx(expected, 2.0e-02)


@pytest.fixture
def sk() -> pyhyperminhash.Sketch:
    sk = pyhyperminhash.Sketch()
    assert not sk
    return sk


@pytest.fixture
def entry() -> pyhyperminhash.Entry:
    e = pyhyperminhash.Entry()
    assert not e
    return e


def test_module():
    assert isinstance(pyhyperminhash.__version__, str)
    assert isinstance(pyhyperminhash.__version_info__(), str)
    assert isinstance(pyhyperminhash.__hyperminhash_version__, str)


def test_Sketch_unhashable(sk: pyhyperminhash.Sketch):
    with pytest.raises(TypeError):
        hash(sk)


def test_constructor(sk: pyhyperminhash.Sketch):
    assert sk.cardinality() == 0.0
    assert len(sk) == 0
    assert int(sk) == 0


def test_eq(sk: pyhyperminhash.Sketch):
    sk2 = pyhyperminhash.Sketch()
    assert sk == sk2
    sk.add("foo")
    assert sk != sk2
    sk2.add("foo")
    assert sk == sk2


def test_cmp(sk: pyhyperminhash.Sketch):
    sk2 = pyhyperminhash.Sketch()
    sk2.add("foo")
    assert sk2 > sk
    assert sk2 >= sk
    assert sk < sk2
    assert sk <= sk2


def test_add(sk: pyhyperminhash.Sketch):
    sk.add("foo")
    assert sk.cardinality() == approx(1.0)
    assert int(sk) == 1
    assert len(sk) == 1

    sk.add("foo")
    assert sk.cardinality() == approx(1.0)
    assert int(sk) == 1
    assert len(sk) == 1

    sk.add(b"bar")
    assert sk.cardinality() == approx(2.0)
    assert int(sk) == 2
    assert len(sk) == 2

    sk.add(b"foobar")
    assert sk.cardinality() == approx(3.0)
    assert int(sk) == 3
    assert len(sk) == 3


def test_add_unhashable(sk: pyhyperminhash.Sketch):
    with pytest.raises(TypeError):
        sk.add(set())  # type: ignore


def test_add_bytes(sk: pyhyperminhash.Sketch):
    for i in range(1000):
        sk.add(b"foo %i" % (i,))
    assert sk.cardinality() == approx(999)


def test_add_reader():
    import io

    s = io.BytesIO()
    s.write(b"foo")
    s.seek(0)
    sk = pyhyperminhash.Sketch()
    assert sk.add_reader(s) == 3


def test_load_and_save(sk: pyhyperminhash.Sketch):
    sk.add("foo")
    sk.add("bar")
    sk.add(1)
    sk.add(2)
    assert len(sk) == 4

    buf = sk.save()
    assert isinstance(buf, bytes)
    assert len(buf) == 2**15

    sk2 = pyhyperminhash.Sketch.load(buf)
    assert len(sk2) == len(sk)


def test_intersection(sk: pyhyperminhash.Sketch):
    for i in range(10000):
        sk.add(b"foo %i" % (i,))
    sk2 = pyhyperminhash.Sketch()
    for i in range(5000, 15000):
        sk2.add(b"foo %i" % (i,))
        sk2.add(b"foo1 %i" % (i,))
    assert sk.intersection(sk2) == approx(5000)


def test_union(sk: pyhyperminhash.Sketch):
    for i in range(100):
        sk.add(b"foo %i" % (i,))
    sk2 = pyhyperminhash.Sketch()
    for i in range(50, 150):
        sk2.add(b"foo %i" % (i,))
        sk2.add(b"foo1 %i" % (i,))
    sk3 = sk & sk2
    assert sk3.cardinality() == approx(250)
    sk &= sk2
    assert len(sk) == len(sk3)


def test_similarity():
    sk1 = pyhyperminhash.Sketch.from_iter(iter(range(0, 10_000)))
    sk2 = pyhyperminhash.Sketch.from_iter(iter(range(5_000, 15_000)))
    assert sk1.similarity(sk2) == approx(5_000.0 / 15_000.0)


def test_from_iter():
    sk = pyhyperminhash.Sketch.from_iter(iter(range(100)))
    assert sk.cardinality() == approx(100)

    sk = pyhyperminhash.Sketch.from_iter(f"foo{i}" for i in range(1000))
    assert sk.cardinality() == approx(1000)


def test_entry_unhashable(entry: pyhyperminhash.Entry):
    with pytest.raises(TypeError):
        hash(entry)


def test_entry_empty(entry: pyhyperminhash.Entry):
    assert not entry
    entry.add(42)
    assert entry


def test_entry_add_unhashable(entry: pyhyperminhash.Entry):
    with pytest.raises(TypeError):
        entry.add(set())  # type: ignore


def test_entry_add(sk: pyhyperminhash.Sketch, entry: pyhyperminhash.Entry):
    entry.add("foo")
    sk.add_entry(entry)
    ln = sk.cardinality()
    assert ln == approx(1)
    sk.add_entry(entry)
    assert sk.cardinality() == ln
    entry.add("foo")
    sk.add_entry(entry)
    assert sk.cardinality() == approx(2)


def test_entry_eq(entry: pyhyperminhash.Entry):
    e2 = pyhyperminhash.Entry()
    assert entry == e2
    entry.add("foo")
    assert entry != e2
    e2.add("foo")
    assert entry == e2


def test_entry_fork(sk: pyhyperminhash.Sketch, entry: pyhyperminhash.Entry):
    entry.add("foo")
    for i in range(5):
        e2 = entry.fork()
        e2.add(i)
        sk.add_entry(e2)
    assert sk.cardinality() == approx(5)

    sk2 = pyhyperminhash.Sketch()
    for i in range(5):
        e1 = pyhyperminhash.Entry()
        e1.add("foo")
        e1.add(i)
        sk2.add_entry(e1)
    assert sk2.cardinality() == sk.cardinality()


def test_entry_consistency(entry: pyhyperminhash.Entry):
    entry.add("a")
    entry.add("a")
    e2 = pyhyperminhash.Entry()
    e2.add("aa")
    assert entry != e2

    e1 = pyhyperminhash.Entry()
    assert e1._digest() == 0x99AA06D3014798D86001C324468D497F
    assert repr(e1) == 'Entry(digest=99aa06d3014798d86001c324468d497f)'
    e1.add_bytes(b"a")
    assert e1._digest() == 0xA96FAF705AF16834E6C632B61E964E1F
    assert repr(e1) == 'Entry(digest=a96faf705af16834e6c632b61e964e1f)'
    e1.add_bytes(b"a")
    assert e1._digest() == 0xB9FE94D346D39B20369242A646A19333
    e2 = pyhyperminhash.Entry()
    e2.add_bytes(b"aa")
    assert e2._digest() == 0xB9FE94D346D39B20369242A646A19333
    assert e1 == e2

    e3 = pyhyperminhash.Entry()
    e3.add_bytes(b"x" * 8191)
    e3.add_bytes(b"x")
    assert e3._digest() == 0xA9F20AE68E5DCB2B9FDB0E2FF17FCC3C


def test_entry_reader_consistency(entry: pyhyperminhash.Entry):
    entry.add_reader(io.BytesIO(b"a"))
    entry.add_reader(io.BytesIO(b"a"))
    e2 = pyhyperminhash.Entry()
    e2.add_reader(io.BytesIO(b"aa"))
    assert entry == e2
