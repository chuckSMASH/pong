#!/usr/bin/env python3
"""
Pong in Pygame (written against Python 3.5)
"""

import math
import random
import sys
from collections import namedtuple

import pygame
from pygame import locals as consts


# Ye olde window constants
FRAMES_PER_SECOND = 40
BACKGROUND_COLOR = (0, 0, 0,)
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1600

# Ball constants
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


class Vector:

    def __init__(self, angle, magnitude):
        self.angle = angle
        self.magnitude = magnitude

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
            y = magnitude * math.sin(math.radians(angle)),
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
        self.vector = Vector(random.randint(140, 220), BALL_MAX_SPEED)
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

    # TODO: don't assume we are on the right side
    def play(self, ball):
        """
        Implement a basic strategy

        Basic strategy:
        ===============
        1) Use geometry (naively - doesn't account for ricochets yet)
        2) Never get tired, never get hungry. Never feel pity. Never
           be moved by a great symphony.
        3) Crush hoomuns.
        """
        angle = ball.vector.angle
        its_coming_right_for_us = not (90 <= angle <= 270)
        is_in_play = (its_coming_right_for_us and
                      ball.rect.left <= self.paddle.rect.left)
        if is_in_play:
            x_distance= self.paddle.rect.left - ball.rect.centerx
            projected_magnitude = math.cos(math.radians(angle)) * x_distance
            projected = Vector(angle, projected_magnitude)
            proj_y = ball.rect.centery + projected.cartesian.y
            if proj_y < self.paddle.rect.top:
                self.paddle.up()
            if proj_y > self.paddle.rect.bottom:
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

    while True:
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if is_quit_event(event):
                pygame.quit()
                sys.exit()

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
        pygame.display.flip()
        clock.tick(FRAMES_PER_SECOND)

    pygame.quit()


if __name__ == '__main__':
    main()
