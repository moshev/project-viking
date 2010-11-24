import project_viking
import unittest

class TestClamp(unittest.TestCase):
    def setUp(self):
        self.clamp01 = project_viking.clamp(0, 1)
        self.clamp38 = project_viking.clamp(3, 8)

    def test_clamping(self):
        numbers = [1, 5, 3, 4, 7, 8, 9, 10, 0.3, -0.8, 38, 99, 100]
        for number in numbers:
            c01 = self.clamp01(number)
            self.assertGreaterEqual(c01, 0)
            self.assertLessEqual(c01, 1)
            c38 = self.clamp38(number)
            self.assertGreaterEqual(c38, 3)
            self.assertLessEqual(c38, 8)

if __name__ == '__main__':
    unittest.main()

