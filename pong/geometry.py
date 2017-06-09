#!/usr/bin/env python3
"""
Useful geometric abstractions
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import math
from collections import namedtuple

import pygame

# Ye olde data structures
Sides = namedtuple('Sides', ['top', 'right', 'bottom', 'left'])
Corners = namedtuple('Corners',
                     ['topleft', 'topright', 'bottomright', 'bottomleft'])
Point = namedtuple('Point', ['x', 'y'])
Line = namedtuple('Line', ['slope', 'intercept'])


class Segment(object):
    '''
    Construct a line segment from two cartesian points
    '''

    def __init__(self, start, end):
        self.start = Point(*start)
        self.end = Point(*end)

    @property
    def line(self):
        '''
        Return the values m and b satisfying y = mx + b

        Values are returned as a tuple (m, b). If the start and
        end points for this segment define a vertical line, this
        function will return (None, None)
        '''
        start, end = self.start, self.end
        diff_x = end.x - start.x
        diff_y = end.y - start.y
        m = (diff_y / diff_x) if diff_x != 0 else None
        b = (start.y - m * start.x) if m is not None else None
        return Line(slope=m, intercept=b)

    @property
    def domain(self):
        return [f(self.start.x, self.end.x) for f in (min, max)]

    @property
    def range(self):
        return [f(self.start.y, self.end.y) for f in (min, max)]

    def in_domain(self, x):
        domain = self.domain
        return domain[0] <= x <= domain[1]

    def in_range(self, y):
        range = self.range
        return range[0] <= y <= range[1]

    def intersection(self, other):
        '''
        Get the intersection of two line segments or None
        '''
        our_line = self.line
        their_line = other.line
        if our_line.slope == their_line.slope:
            # we are parallel
            return None
        if our_line.slope is None:
            # we are vertical
            x = self.start.x
            y = their_line.slope * x + their_line.intercept
        elif their_line.slope is None:
            # they are vertical
            x = other.start.x
            y = our_line.slope * x + our_line.intercept
        else:
            x = (
                (their_line.intercept - our_line.intercept) /
                (our_line.slope - their_line.slope)
            )
            y = our_line.slope * x + our_line.intercept

        if all(seg.in_domain(x) and seg.in_range(y) for seg in (self, other)):
            return Point(x, y)
        return None


class Rect(object):
    '''
    Towards modelling our own rects independent of screen pixels
    '''

    def __init__(self, left, top, width, height, color=None):
        self.left = left
        self.top = top
        self.height = height
        self.width = width
        self.color = color

    def __repr__(self):
        return '<Rect (x: {}, y: {}, w: {}, h: {})>'.format(
            self.left,
            self.top,
            self.width,
            self.height)

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def center(self):
        return Point(
            self.left + (self.width / 2),
            self.top + (self.height / 2)
        )

    @right.setter
    def right(self, value):
        self.left = value - self.width

    @bottom.setter
    def bottom(self, value):
        self.top = value - self.height

    @property
    def corners(self):
        return Corners(
            topleft=Point(self.left, self.top),
            topright=Point(self.right, self.top),
            bottomright=Point(self.right, self.bottom),
            bottomleft=Point(self.left, self.bottom),
        )

    @property
    def segments(self):
        corners = self.corners
        return Sides(
            top=Segment(corners.topleft, corners.topright),
            right=Segment(corners.topright, corners.bottomright),
            bottom=Segment(corners.bottomleft, corners.bottomright),
            left=Segment(corners.topleft, corners.bottomleft)
        )

    def contains(self, other):
        return (
            self.left < other.left and
            self.top < other.top and
            self.right > other.right and
            self.bottom > other.bottom
        )

    def collides(self, other):
        has_collisions = (
            self.left <= other.right and  # we aren't entirely to other's right
            self.right >= other.left and  # nor entirely to other's left
            self.top <= other.bottom and  # nor entirely above
            self.bottom >= other.top      # nor entirely below
        )
        return has_collisions

    def get_uncontained_edges(self, containing_rect):
        if containing_rect.contains(self):
            return Sides(False, False, False, False)
        return Sides(
            top=(self.top <= containing_rect.top),
            right=(self.right >= containing_rect.right),
            bottom=(self.bottom >= containing_rect.bottom),
            left=(self.left <= containing_rect.left),
        )

    def get_overlapping_edges(self, other):
        if not self.collides(other):
            return Sides(False, False, False, False)
        left = other.left <= self.left <= other.right
        right = other.left <= self.right <= other.right
        top = other.top <= self.top <= other.bottom
        bottom = other.top <= self.bottom <= other.bottom
        return Sides(top=top, right=right, bottom=bottom, left=left)

    def move(self, vector):
        x, y = vector.cartesian
        self.left += x
        self.top += y

    def draw(self, surface):
        image = pygame.Surface((self.width, self.height))
        image.fill(self.color)
        image_rect = image.get_rect(top=self.top, left=self.left)
        surface.blit(image, image_rect)


class Vector(object):

    def __init__(self, angle, magnitude):
        self.angle = angle % 360
        self.magnitude = magnitude

    def __repr__(self):
        return '<Vector (a: {}, m: {} x: {}, y: {})>'.format(
            self.angle,
            self.magnitude,
            *self.cartesian)

    @classmethod
    def from_cartesian(cls, x, y):
        magnitude = math.sqrt(x**2 + y**2)
        y = -y
        if x == 0:
            angle = 90 if y >= 0 else 270
        else:
            angle = math.degrees(math.atan(y / x))
            if y < 0 or x < 0:
                angle += 180
                if x > 0:
                    angle += 180
            angle %= 360
        return cls(angle, magnitude)

    @property
    def cartesian(self):
        magnitude = self.magnitude
        angle = self.angle
        x = magnitude * math.cos(math.radians(angle))
        y = -magnitude * math.sin(math.radians(angle))
        if angle == 0:
            x = magnitude
        if angle == 90:
            y = -magnitude
        if angle == 180:
            x = -magnitude
        if angle == 270:
            y = magnitude
        return Point(x, y)

    def reflect(self, horizontally=False, vertically=False):
        normed_angle = self.angle % 360
        if horizontally:
            normed_angle = (360 - (normed_angle - 180)) % 360
        if vertically:
            normed_angle = 360 - normed_angle
        return self.__class__(normed_angle, self.magnitude)
