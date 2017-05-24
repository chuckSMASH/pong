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


# Ye olde constants
FRAMES_PER_SECOND = 40
BACKGROUND_COLOR = (0, 0, 0,)
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1600

BALL_MIN_SPEED = 10
BALL_MAX_SPEED = 30
BALL_HEIGHT = 20
BALL_WIDTH = 20
BALL_COLOR = (127, 216, 127,)

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
        self.vector = Vector(random.randint(0, 360), BALL_MAX_SPEED)
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


class PlayerPaddle(Paddle):

    def __init__(self, top, left):
        super().__init__(top, left)
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

    def update(self):
        if self.is_moving:
            self.rect.move_ip(0, self.speed * self.direction)
            self.is_moving = False


class AutoPaddle(Paddle):

    def __init__(self, top, left):
        super().__init__(top, left)
        self.direction = random.choice((-1, 1))
        self.speed = 0

    def should_change_direction(self):
        return random.random() >= .99

    def update(self):
        self.speed = random.uniform(PADDLE_MIN_SPEED, PADDLE_MAX_SPEED)
        if self.should_change_direction():
            self.direction *= -1
        self.rect.move_ip(0, self.direction * self.speed)
        if self.rect.top < 0:
            self.direction *= -1
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.direction *= -1
            self.rect.bottom = SCREEN_HEIGHT


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

    paddle1 = PlayerPaddle(50, 100)
    paddle2 = AutoPaddle(50, screen.get_rect().width - 110)
    ball = Ball()
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

        ball.check_paddle_collision(paddle1)
        ball.check_paddle_collision(paddle2)

        screen.blit(background, (0, 0))
        ball.update()
        paddle1.update()
        paddle2.update()
        screen.blit(ball.image, ball.rect)
        screen.blit(paddle1.image, paddle1.rect)
        screen.blit(paddle2.image, paddle2.rect)
        pygame.display.flip()
        clock.tick(FRAMES_PER_SECOND)

    pygame.quit()


if __name__ == '__main__':
    main()
