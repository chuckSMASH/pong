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
            point = pong.Cartesian(cos, -sin)
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
