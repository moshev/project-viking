import orbitals
import unittest

class TestArrayStore(unittest.TestCase):
    def setUp(self):
        self.store = orbitals.arraystore((2,))

    def test_alloc(self):
        iarr1 = self.store.alloc()
        self.assertEqual(False, self.store.free[iarr1])
        arr = self.store.array[iarr1]
        self.assertEqual(0.0, arr[0])
        self.assertEqual(0.0, arr[1])

        iarr2 = self.store.alloc()
        self.assertNotEqual(iarr1, iarr2)
        self.assertEqual(False, self.store.free[iarr2])
        arr = self.store.array[iarr2]
        self.assertEqual(0.0, arr[0])
        self.assertEqual(0.0, arr[1])

if __name__ == '__main__':
    unittest.hitboxeditor_main()

