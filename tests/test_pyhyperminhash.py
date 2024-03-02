import unittest

import pyhyperminhash


class TestPyhyperminhash(unittest.TestCase):

    def test_version(self):
        self.assertIsInstance(pyhyperminhash.__version__, str)

    def test_version_info(self):
        self.assertIsInstance(pyhyperminhash.__version_info__(), str)

    def test_hyperminhash_version(self):
        self.assertIsInstance(pyhyperminhash.__hyperminhash_version__, str)


class TestSketch(unittest.TestCase):

    def test_constructor(self):
        sk = pyhyperminhash.Sketch()
        self.assertFalse(sk)
        self.assertEqual(sk.cardinality(), 0.0)
        self.assertEqual(len(sk), 0)
        self.assertEqual(int(sk), 0)

    def test_add(self):
        sk = pyhyperminhash.Sketch()
        self.assertFalse(sk)
        self.assertEqual(sk.cardinality(), 0.0)
        sk.add('foo')
        self.assertTrue(sk)
        self.assertAlmostEqual(sk.cardinality(), 1.0, 2)
        self.assertEqual(int(sk), 1)
        self.assertEqual(len(sk), 1)
        sk.add('foo')
        self.assertAlmostEqual(sk.cardinality(), 1.0, 2)
        self.assertEqual(int(sk), 1)
        self.assertEqual(len(sk), 1)
        sk += 'foo2'
        self.assertAlmostEqual(sk.cardinality(), 2.0, 2)
        self.assertAlmostEqual(float(sk), 2.0, 2)
        self.assertEqual(int(sk), 2)
        self.assertEqual(len(sk), 2)

    def test_load_and_save(self):
        sk = pyhyperminhash.Sketch()
        sk.add('foo')
        sk.add('bar')
        sk.add(1)
        sk.add(2)
        self.assertEqual(len(sk), 4)

        buf = sk.save()
        self.assertIsInstance(buf, bytes)
        self.assertEqual(len(buf), 2**15)

        sk2 = pyhyperminhash.Sketch.load(buf)
        self.assertEqual(len(sk2), 4)

    def test_add_bytes(self):
        sk = pyhyperminhash.Sketch()
        for i in range(100):
            sk.add_bytes(b'foo %i' % (i, ))
        self.assertEqual(len(sk), 99)

    def test_union(self):
        sk1 = pyhyperminhash.Sketch()
        for i in range(100):
            sk1.add_bytes(b'foo %i' % (i, ))
        sk2 = pyhyperminhash.Sketch()
        for i in range(50, 150):
            sk2.add_bytes(b'foo %i' % (i, ))
            sk2.add_bytes(b'foo1 %i' % (i, ))
        sk3 = sk1 & sk2
        self.assertEqual(len(sk3), 250)
        sk1 &= sk2
        self.assertEqual(len(sk1), len(sk3))

    def test_intersection(self):
        sk1 = pyhyperminhash.Sketch()
        for i in range(10000):
            sk1.add_bytes(b'foo %i' % (i, ))
        sk2 = pyhyperminhash.Sketch()
        for i in range(5000, 15000):
            sk2.add_bytes(b'foo %i' % (i, ))
            sk2.add_bytes(b'foo1 %i' % (i, ))
        self.assertAlmostEqual(sk1.intersection(sk2) / 1000, 5, 1)

    def test_hash_eq(self):
        sk1 = pyhyperminhash.Sketch()
        sk2 = pyhyperminhash.Sketch()
        self.assertEqual(sk1, sk2)
        self.assertEqual(hash(sk1), hash(sk2))
        sk1.add('foo')
        self.assertNotEqual(sk1, sk2)
        self.assertNotEqual(hash(sk1), hash(sk2))
        sk2.add('foo')
        self.assertEqual(sk1, sk2)
        self.assertEqual(hash(sk1), hash(sk2))
        sk2.add('foo')
        self.assertEqual(sk1, sk2)
        self.assertEqual(hash(sk1), hash(sk2))
        sk2.add('bar')
        self.assertNotEqual(sk1, sk2)
        self.assertNotEqual(hash(sk1), hash(sk2))
