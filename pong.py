#!/usr/bin/env python3
"""
Pong in Pygame (written against Python 3.5)
"""

import argparse
import math
import random
import sys
from collections import namedtuple
from textwrap import dedent

import pygame
from pygame import locals as consts


global DEBUG
DEBUG_PATH_COLOR = (128, 0, 0,)

# Ye olde window constants
FRAMES_PER_SECOND = 40
BACKGROUND_COLOR = (0, 0, 0,)
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1600

# Ball constants
BALL_START_ANGLE = 62
BALL_MIN_SPEED = 10
BALL_MAX_SPEED = 30
BALL_HEIGHT = 20
BALL_WIDTH = 20
BALL_COLOR = (127, 216, 127,)

# Paddle constants
PADDLE_MIN_SPEED = 10
PADDLE_MAX_SPEED = 20
PADDLE_HEIGHT = 150
PADDLE_WIDTH = 30
PADDLE_COLOR = (127, 216, 127,)
PADDLE_DOWN_DIR = 1
PADDLE_UP_DIR = -1


# Ye olde data structures
Sides = namedtuple('Sides', ['top', 'right', 'bottom', 'left'])
Cartesian = namedtuple('Cartesian', ['x', 'y'])


class Path:

    def __init__(self):
        self.points = []

    def __repr__(self):
        return '<Path ({})>'.format(','.join(self.points))

    def add(self, point):
        self.points.append(point)

    def clear(self):
        self.points = []


class Vector:

    def __init__(self, angle, magnitude):
        self.angle = angle
        self.magnitude = magnitude

    def __repr__(self):
        return '<Vector (a: {}, m: {} x: {}, y: {})>'.format(
            self.angle,
            self.magnitude,
            *self.cartesian)

    @classmethod
    def from_cartesian(x, y):
        self.magnitude = math.sqrt(x**2 + y**2)
        if x != 0:
            self.angle = math.degrees(math.atan(y / x))
        else:
            self.angle = 90 if y >= 0 else 270

    @property
    def cartesian(self):
        magnitude = self.magnitude
        angle = self.angle
        return Cartesian(
            x = magnitude * math.cos(math.radians(angle)),
            y = -magnitude * math.sin(math.radians(angle)),
        )

    def reflect(self, horizontally=False, vertically=False):
        normed_angle = self.angle % 360
        if horizontally:
            normed_angle = (360 - (normed_angle - 180)) % 360
        if vertically:
            normed_angle = 360 - normed_angle
        return self.__class__(normed_angle, self.magnitude)


class Ball:

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BALL_WIDTH, BALL_HEIGHT))
        self.image.fill(BALL_COLOR)
        center_vert = SCREEN_HEIGHT // 2 - (BALL_HEIGHT // 2)
        center_horiz = SCREEN_WIDTH // 2 - (BALL_WIDTH // 2)
        self.rect = self.image.get_rect().move(center_horiz, center_vert)
        angle = BALL_START_ANGLE or random.randint(0, 360)
        self.vector = Vector(angle, BALL_MAX_SPEED)
        self.touching_paddle = False

    def calc_sides_touched(self):
        return Sides(
            top = self.rect.top <= 0,
            right = self.rect.right >= SCREEN_WIDTH,
            bottom = self.rect.bottom >= SCREEN_HEIGHT,
            left = self.rect.left <= 0,
        )

    def check_paddle_collision(self, paddle):
        if pygame.sprite.collide_rect(self, paddle):
            self.touching_paddle = True

    def should_change_direction(self):
        screen_area = pygame.display.get_surface().get_rect()
        return not screen_area.contains(self.rect) or self.touching_paddle

    def update(self):
        if self.should_change_direction():
            sides_touched = self.calc_sides_touched()
            if any(sides_touched):
                reflect_h = sides_touched.left or sides_touched.right
                reflect_v = sides_touched.top or sides_touched.bottom
            else:
                reflect_h = True
                reflect_v = False
            self.vector = self.vector.reflect(reflect_h, reflect_v)
        self.rect.move_ip(*self.vector.cartesian)
        self.touching_paddle = False


class Paddle:

    def __init__(self, top, left):
        super().__init__()
        self.height = PADDLE_HEIGHT
        self.width = PADDLE_WIDTH
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(PADDLE_COLOR)
        self.rect = self.image.get_rect().move(left, top)
        self.speed = 0
        self.direction = 0
        self.is_moving = False

    def up(self):
        self.is_moving = True
        self.direction = PADDLE_UP_DIR
        self.speed = PADDLE_MAX_SPEED

    def down(self):
        self.is_moving = True
        self.direction = PADDLE_DOWN_DIR
        self.speed = PADDLE_MAX_SPEED

    def recenter(self):
        self.is_moving = True
        d_center = self.rect.centery - (SCREEN_HEIGHT // 2)
        self.direction = PADDLE_DOWN_DIR if d_center < 0 else PADDLE_UP_DIR
        self.speed = min(PADDLE_MAX_SPEED, abs(d_center))

    def update(self):
        if self.is_moving:
            self.rect.move_ip(0, self.speed * self.direction)
            self.is_moving = False


class MercilessAutomaton:

    def __init__(self, paddle):
        self.paddle = paddle
        self.prediction = Path()
        self.sweet_spot_radius = self.paddle.rect.height // 4

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
        intercept = Cartesian(intercept_x, proj_y)
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
        # calc TAN to find the length of the adjacent side which
        # is the x-value at which the vector leaves the screen
        new_diff_y = abs(next_y - y)
        new_diff_x = abs(
            math.tan(math.radians(90 - (angle % 180))) * new_diff_y)

        new_start = Cartesian(x + new_diff_x, next_y)
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
            ball_location = Cartesian(*ball.rect.center)
            intercept = self.predict_intercept(
                ball_location, ball.vector, self.paddle.rect.left)
            sweet_spot = Sides(
                top=self.paddle.rect.centery - self.sweet_spot_radius,
                bottom=self.paddle.rect.centery + self.sweet_spot_radius,
                left=None,
                right=None,
            )
            if intercept and intercept.y < sweet_spot.top:
                self.paddle.up()
            if intercept and intercept.y > sweet_spot.bottom:
                self.paddle.down()
        else:
            self.paddle.recenter()


def is_quit_event(e):
    return (
        e.type == consts.QUIT or
        (e.type == consts.KEYDOWN and e.key == consts.K_ESCAPE)
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('pong')
    pygame.mouse.set_visible(False)

    background = pygame.Surface(screen.get_size())
    background.fill(BACKGROUND_COLOR)
    screen.blit(background, (0, 0))

    paddle1 = Paddle(50, 100)
    paddle2 = Paddle(50, screen.get_rect().width - 110)
    computer = MercilessAutomaton(paddle2)
    ball = Ball()
    all_sprites = (paddle1, paddle2, ball,)
    clock = pygame.time.Clock()

    if DEBUG:
        import pdb

    while True:
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if is_quit_event(event):
                pygame.quit()
                sys.exit()

        if DEBUG and keys[ord('d')]:
            pdb.set_trace()

        if keys[consts.K_UP]:
            paddle1.up()
        elif keys[consts.K_DOWN]:
            paddle1.down()

        computer.play(ball)
        ball.check_paddle_collision(paddle1)
        ball.check_paddle_collision(paddle2)

        screen.blit(background, (0, 0))
        for sprite in all_sprites:
            sprite.update()
            screen.blit(sprite.image, sprite.rect)

        if DEBUG and len(computer.prediction.points) > 1:
            pygame.draw.lines(screen, DEBUG_PATH_COLOR, False,
                              computer.prediction.points, 3)
        pygame.display.flip()
        clock.tick(FRAMES_PER_SECOND)

    pygame.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug', action='store_true',
        help=dedent(
            '''\
            Run the game in debug mode. This will cause the
            computer player's prediction of the ball's path
            to be drawn on the screen in red.

            Additionally, when in debug mode pressing the 'd'
            key will pause the simulation with a breakpoint
            set at the beginning of the event loop.
            '''))
    args = parser.parse_args()
    global DEBUG
    DEBUG = args.debug
    main()
