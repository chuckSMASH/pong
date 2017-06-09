"""
Game-level constructs
"""

import math
from collections import OrderedDict
from collections import namedtuple

import pygame
from pygame import locals as consts

from pong.geometry import Corners
from pong.geometry import Point
from pong.geometry import Rect
from pong.geometry import Segment
from pong.geometry import Sides
from pong.geometry import Vector


global DEBUG
DEBUG_PATH_COLOR = (128, 0, 0,)

# Ye olde data structures
Color = namedtuple('Color', ['r', 'g', 'b'])

# Ye olde window constants
BASE_FPS = 60
FRAMES_PER_SECOND = 60
BACKGROUND_COLOR = Color(r=0, g=0, b=0)
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1600

# Ball constants
BALL_START_ANGLE = 48
BALL_MIN_SPEED = 20 * BASE_FPS / FRAMES_PER_SECOND
BALL_MAX_SPEED = 80 * BASE_FPS / FRAMES_PER_SECOND
BALL_SPEED_INCR = 1 * BASE_FPS / FRAMES_PER_SECOND
BALL_MIN_ANGLE = 20
BALL_MAX_ANGLE = 70
BALL_HEIGHT = 20
BALL_WIDTH = 20
BALL_COLOR = Color(r=127, g=216, b=127)

# Paddle constants
PADDLE_MIN_SPEED = 24 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_MAX_SPEED = 40 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_SPEED_INCR = 2 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_SPEED_DECR = 4 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_HEIGHT = 120
PADDLE_WIDTH = 10
PADDLE_COLOR = Color(r=127, g=216, b=127)
PADDLE_DOWN_DIR = 1
PADDLE_UP_DIR = -1

# Sauce constants
SAUCE_MULTIPLIER = 30
SAUCE_MAX = SAUCE_MULTIPLIER // 2
SAUCE_MIN = -SAUCE_MAX

# Action constants
PADDLE_UP = 'PADDLE_UP'
PADDLE_DOWN = 'PADDLE_DOWN'

# Key maps
PLAYER1_KEY_MAP = {
    consts.K_UP: PADDLE_UP,
    consts.K_DOWN: PADDLE_DOWN,
}

PLAYER2_KEY_MAP = {
    consts.K_w: PADDLE_UP,
    consts.K_s: PADDLE_DOWN,
}

# Menu constants
MENU_OPTIONS = OrderedDict([
    ('1 Player', 1,),
    ('2 Players', 2,),
])


class Player(object):

    def __init__(self, key_map, paddle):
        self.key_map = key_map
        self.paddle = paddle
        self.actions = {
            PADDLE_UP: self.paddle.up,
            PADDLE_DOWN: self.paddle.down,
        }
        self.is_human = True

    def dispatch(self, keys_pressed):
        for key, action in self.key_map.items():
            if keys_pressed[key]:
                self.actions.get(action, lambda: None)()


class Path(object):

    def __init__(self):
        self.points = []
        self.color = DEBUG_PATH_COLOR

    def __repr__(self):
        return '<Path ({})>'.format(','.join(self.points))

    def add(self, point):
        self.points.append(point)

    def clear(self):
        self.points = []

    def draw(self, screen):
        pygame.draw.lines(screen, self.color, False, self.points, 3)


class Ball(object):

    def __init__(self):
        left = SCREEN_WIDTH // 2 - (BALL_WIDTH // 2)
        top = SCREEN_HEIGHT // 2 - (BALL_HEIGHT // 2)
        self.rect = Rect(left, top, BALL_WIDTH, BALL_HEIGHT, BALL_COLOR)
        self.vector = Vector(BALL_START_ANGLE, BALL_MIN_SPEED)
        self.sauce = 0

    def handle_screen_edges(self, screen_rect):
        uncontained = self.rect.get_uncontained_edges(screen_rect)
        reflect_h = uncontained.left or uncontained.right
        reflect_v = uncontained.top or uncontained.bottom
        if uncontained.bottom:
            self.rect.bottom = SCREEN_HEIGHT - 1
        elif uncontained.top:
            self.rect.top = 1
        self.vector = self.vector.reflect(reflect_h, reflect_v)

    def handle_paddle_collision(self, paddle):
        going_left = 90 < self.vector.angle < 270
        going_up = 0 < self.vector.angle < 180
        ball_y = self.rect.center.y
        paddle_sides = paddle.rect.segments
        delta = self.vector.cartesian
        ball_corners = Corners(*[
            Segment(
                corner,
                Point(corner.x + delta.x, corner.y + delta.y))
            for corner in self.rect.corners
        ])
        hits = Sides(*[
            next(
                filter(
                    lambda c: c,
                    [corner.intersection(side) for corner in ball_corners]
                ), None
            )
            for side in paddle_sides
        ])
        if any(hits):
            self.vector = self.vector.reflect(horizontally=True)
            if going_left and hits.right:
                self.rect.left = hits.right.x + 1
                self.rect.top = hits.right.y
            elif not going_left and hits.left:
                self.rect.right = hits.left.x - 1
                self.rect.top = hits.left.y

            if hits.bottom and going_up:
                self.rect.top = hits.bottom.y
                self.vector = self.vector.reflect(vertically=True)
            elif hits.top and not going_up:
                self.rect.bottom = hits.top.y
                self.vector = self.vector.reflect(vertically=True)
            diff_y = paddle.rect.center.y - ball_y
            sauce = round((diff_y / paddle.rect.height) * SAUCE_MULTIPLIER)
            self.vector.magnitude = min(
                self.vector.magnitude + BALL_SPEED_INCR,
                BALL_MAX_SPEED)
            self.sauce = min(SAUCE_MAX, max(SAUCE_MIN, sauce * going_up))

    def apply_sauce(self, vector, sauce):
        angle = vector.angle
        abs_from_x_axis = 90 - abs(90 - (angle % 180))
        # account for quadrant. the quadrant we are in impacts
        # +/- and flattening/steepening behavior
        direction = 1 if angle % 180 < 90 else -1
        mellow_sauce = min(BALL_MAX_ANGLE - abs_from_x_axis,
                           max(direction * sauce,
                               BALL_MIN_ANGLE - abs_from_x_axis))
        return Vector(vector.angle + mellow_sauce, vector.magnitude)

    def update(self):
        if self.sauce != 0:
            self.vector = self.apply_sauce(self.vector, self.sauce)
            self.sauce = 0
        else:
            self.rect.move(self.vector)

    def draw(self, surface):
        self.rect.draw(surface)


class Paddle(object):

    def __init__(self, left, top):
        self.rect = Rect(left, top, PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_COLOR)
        self.vector = Vector(90, 0)
        self.moved = False

    def up(self):
        self.moved = True
        prev_vector = self.vector
        if prev_vector.angle == 90:
            speed = self.accelerate(prev_vector.magnitude)
        else:
            speed = PADDLE_MIN_SPEED
        diff_y = self.rect.top
        self.vector = Vector(90, min(diff_y, speed))

    def down(self):
        self.moved = True
        prev_vector = self.vector
        if prev_vector.angle == 270:
            speed = self.accelerate(prev_vector.magnitude)
        else:
            speed = PADDLE_MIN_SPEED
        diff_y = SCREEN_HEIGHT - self.rect.bottom
        self.vector = Vector(270, min(diff_y, speed))

    def recenter(self):
        self.moved = True
        d_center = self.rect.center.y - (SCREEN_HEIGHT // 2)
        prev_vector = self.vector
        direction = PADDLE_DOWN_DIR if d_center < 0 else PADDLE_UP_DIR
        turned_around = (
            (prev_vector.angle == 270 and direction == PADDLE_UP_DIR) or
            (prev_vector.angle == 90 and direction == PADDLE_DOWN_DIR))
        if turned_around:
            speed = PADDLE_MIN_SPEED
        else:
            speed = self.accelerate(prev_vector.magnitude)
        speed = min(speed, abs(d_center))
        self.vector = Vector.from_cartesian(0, direction*speed)

    def accelerate(self, prev_speed):
        return min(
            PADDLE_MAX_SPEED,
            prev_speed + PADDLE_SPEED_INCR)

    def decelerate(self, prev_speed):
        return max(
            0,
            prev_speed - PADDLE_SPEED_DECR)

    def update(self):
        if not self.moved:
            speed = self.decelerate(self.vector.magnitude)
            self.vector = Vector(self.vector.angle, speed)
        self.moved = False
        self.rect.move(self.vector)
        if self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

    def draw(self, surface):
        self.rect.draw(surface)


class MercilessAutomaton:

    def __init__(self, paddle):
        self.paddle = paddle
        self.is_human = False
        self.prediction = Path()
        self.sweet_spot_radius = self.paddle.rect.height // 2

    # TODO: don't assume we are on the right side
    def predict_intercept(self, start, vector, intercept_x, max_reflections=5):
        """
        Predict where the ball will intercept our paddle

        max_reflections specifies the maximum number of bounces off
        the top or bottom of the screen we are willing to calculate
        ahead of time. This estimate will be a little inaccurate if
        start and vector are calculated from the center of the ball
        because the bounce is calculated from the edges
        """
        x, y = start
        diff_x = intercept_x - x
        angle = vector.angle
        magnitude = diff_x / math.cos(math.radians(angle))
        projected = Vector(angle, magnitude)
        proj_y = y + projected.cartesian.y
        intercept = Point(intercept_x, proj_y)
        self.prediction.add(start)

        if 0 <= proj_y <= SCREEN_HEIGHT:
            self.prediction.add(intercept)
            return intercept
        elif max_reflections == 0:
            return None

        if proj_y < 0:
            next_y = 0
        else:
            next_y = SCREEN_HEIGHT

        # if a calculated trajectory doesn't intercept our paddle's
        # movement axis on-screen, we calculate the approximate
        # intercept between the vector and the top/bottom edge of the
        # screen, reflect the vector vertically and then see if that
        # gets us within spitting distance our paddle's movement axis.
        #
        # kind of wonky looking math. breaking it down:
        #
        # 90 - (angle % 180): get angle of vector compared to y-axis
        # abs: only interested in dist, not direction
        # Now our angle is that between the vector and the y-axis; our
        # new_diff_y is the length of the side adjacent to that angle; we
        # calc TAN to find the length of the opposite side which
        # is the x-value at which the vector leaves the screen.
        new_diff_y = abs(next_y - y)
        new_diff_x = abs(
            math.tan(math.radians(90 - (angle % 180))) * new_diff_y)

        new_start = Point(x + new_diff_x, next_y)
        new_vector = vector.reflect(vertically=True)
        return self.predict_intercept(new_start, new_vector, intercept_x,
                                      max_reflections-1)

    # TODO: don't assume we are on the right side
    def play(self, ball):
        """
        Implement a basic strategy

        Basic strategy:
        ===============
        1) Use geometry
        2) Never get tired, never get hungry. Never feel pity. Never
           be moved by a great symphony.
        3) Crush hoomuns.
        """
        self.prediction.clear()
        angle = ball.vector.angle
        its_coming_right_for_us = not (90 <= angle <= 270)
        is_in_play = (its_coming_right_for_us and
                      ball.rect.left <= self.paddle.rect.left)
        if is_in_play:
            ball_location = Point(*ball.rect.center)
            intercept = self.predict_intercept(
                ball_location, ball.vector, self.paddle.rect.left)
            sweet_spot = Sides(
                top=self.paddle.rect.center.y - self.sweet_spot_radius,
                bottom=self.paddle.rect.center.y + self.sweet_spot_radius,
                left=None,
                right=None,
            )
            if intercept and intercept.y < sweet_spot.top:
                self.paddle.up()
            if intercept and intercept.y > sweet_spot.bottom:
                self.paddle.down()
        else:
            self.paddle.recenter()
