import math
import unittest

import pong


class RectTestCase(unittest.TestCase):

    def setUp(self):
        self.rect1 = pong.Rect(15, 20, 60, 80)
        # rect2 overlaps rect1
        self.rect2 = pong.Rect(13, 19, 10, 10)
        # rect3 is contained by rect1
        self.rect3 = pong.Rect(16, 21, 10, 10)


    def test_repr(self):
        self.assertEqual(
            repr(self.rect1),
            '<Rect (x: 15, y: 20, w: 60, h: 80)>')

    def test_attributes(self):
        self.assertEqual(self.rect1.left, 15)
        self.assertEqual(self.rect1.top, 20)

    def test_properties(self):
        self.assertEqual(self.rect1.right, 75)
        self.assertEqual(self.rect1.bottom, 100)
        self.assertEqual(self.rect1.center.x, 45)
        self.assertEqual(self.rect1.center.y, 60)

    def test_contains(self):
        self.assertTrue(self.rect1.contains(self.rect3))
        self.assertFalse(self.rect1.contains(self.rect2))


class VectorTestCase(unittest.TestCase):

    def setUp(self):
        self.points = []
        self.vectors = []
        self.cart_vectors = []
        for angle in range(0, 361, 3):
            cos = math.cos(math.radians(angle))
            sin = math.sin(math.radians(angle))
            point = pong.Point(cos, -sin)
            vector = pong.Vector(angle, 1)
            cart_vector = pong.Vector.from_cartesian(*point)
            self.points.append(point)
            self.vectors.append(vector)
            self.cart_vectors.append(cart_vector)

    def test_init(self):
        vector = pong.Vector(-15, 1)
        self.assertAlmostEqual(vector.angle, 345)

    def test_from_cartesian(self):
        for polar, cart in zip(self.vectors, self.cart_vectors):
            self.assertAlmostEqual(polar.angle, cart.angle)
            self.assertAlmostEqual(polar.magnitude, cart.magnitude)

    def test_to_cartesian(self):
        for polar, point in zip(self.vectors, self.points):
            as_cart = polar.cartesian
            self.assertAlmostEqual(as_cart.x, point.x)
            self.assertAlmostEqual(as_cart.y, point.y)

        for cart, point in zip(self.cart_vectors, self.points):
            as_cart = cart.cartesian
            self.assertAlmostEqual(as_cart.x, point.x)
            self.assertAlmostEqual(as_cart.y, point.y)

    def test_reflect(self):
        for vector in self.vectors:
            vert = vector.reflect(vertically=True)
            horiz = vector.reflect(horizontally=True)
            both = vector.reflect(vertically=True, horizontally=True)
            revert = vert.reflect(vertically=True)
            rehoriz = horiz.reflect(horizontally=True)
            combo1 = vert.reflect(horizontally=True)
            combo2 = horiz.reflect(vertically=True)
            self.assertAlmostEqual(revert.angle, vector.angle)
            self.assertAlmostEqual(rehoriz.angle, vector.angle)
            self.assertAlmostEqual(combo1.angle, combo2.angle)
            self.assertAlmostEqual(combo1.angle, both.angle)


class SegmentTestCase(unittest.TestCase):

    def setUp(self):
        P = pong.Point
        self.s1 = pong.Segment(P(0, 0), P(1, 1))
        self.s2 = pong.Segment(P(0, 1), P(1, 0))
        self.s3 = pong.Segment(P(0, -1), P(1, 0))
        self.s4 = pong.Segment(P(1, 1), P(2, 2))

    def test_line(self):
        s1_line = self.s1.line
        s2_line = self.s2.line
        s3_line = self.s3.line
        self.assertEqual(s1_line.slope, 1)
        self.assertEqual(s1_line.intercept, 0)
        self.assertEqual(s2_line.slope, -1)
        self.assertEqual(s2_line.intercept, 1)
        self.assertEqual(s3_line.slope, 1)
        self.assertEqual(s3_line.intercept, -1)

    def test_intersection(self):
        P = pong.Point
        actual_expected = [
            (self.s1.intersection(self.s2), P(0.5, 0.5)),
            (self.s2.intersection(self.s1), P(0.5, 0.5)),
            (self.s1.intersection(self.s3), None),
            (self.s3.intersection(self.s1), None),
            (self.s1.intersection(self.s4), None),
            (self.s4.intersection(self.s1), None),
            (self.s2.intersection(self.s3), P(1, 0)),
            (self.s3.intersection(self.s2), P(1, 0)),
            (self.s2.intersection(self.s4), None),
            (self.s4.intersection(self.s2), None),
            (self.s3.intersection(self.s4), None),
            (self.s4.intersection(self.s3), None),
        ]
        for actual, expected in actual_expected:
            if expected is None:
                self.assertIsNone(actual)
            else:
                for actual_coord, expected_coord in zip(actual, expected):
                    self.assertAlmostEqual(actual_coord, expected_coord)
