#!/usr/bin/env python3

import math
import random
import sys
from collections import namedtuple

import pygame
from pygame import locals as consts


# Ye olde constants
FPS = 40
BACKGROUND_COLOR = (240, 240, 240,)
SCREEN_HEIGHT = 1000
SCREEN_WIDTH = 1600

BALL_MAX_SPEED = 30
BALL_HEIGHT = 20
BALL_WIDTH = 20
BALL_COLOR = (127, 216, 127,)

PADDLE_MAX_SPEED = 20
PADDLE_HEIGHT = 150
PADDLE_WIDTH = 30
PADDLE_COLOR = (127, 216, 127,)


# Ye olde data structures
Sides = namedtuple('Sides', ['top', 'right', 'bottom', 'left'])
Direction = namedtuple('Direction', ['x', 'y'])


class Ball:
    speed = BALL_MAX_SPEED

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BALL_WIDTH, BALL_HEIGHT))
        self.image.fill(BALL_COLOR)
        center_vert = SCREEN_HEIGHT // 2 - (BALL_HEIGHT / 2)
        center_horiz = SCREEN_WIDTH // 2 - (BALL_WIDTH / 2)
        self.rect = self.image.get_rect().move(center_horiz, center_vert)
        self.angle = random.randint(0, 360)
        self.touching_paddle = False
        self._direction = None

    @property
    def direction(self):
        if not self._direction:
            self._direction = Direction(
                x = math.cos(math.radians(self.angle)),
                y = math.sin(math.radians(self.angle)),
            )
        return self._direction

    def calc_reflection(self, angle, reflect_h=False, reflect_v=False):
        normed_angle = angle % 360
        if reflect_h:
            normed_angle = (360 - (normed_angle - 180)) % 360
        if reflect_v:
            normed_angle = 360 - normed_angle
        return normed_angle

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
            self.angle = self.calc_reflection(self.angle, reflect_h, reflect_v)
            self._direction = None
        horiz, vert = self.direction
        self.rect.move_ip(horiz * self.speed, vert * self.speed)
        self.touching_paddle = False


class Paddle:
    height = PADDLE_HEIGHT
    width = PADDLE_WIDTH

    def __init__(self, top, left):
        super().__init__()

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(PADDLE_COLOR)
        self.rect = self.image.get_rect().move(left, top)


class PlayerPaddle(Paddle):
    speed = PADDLE_MAX_SPEED

    def __init__(self, top, left):
        super().__init__(top, left)
        self.direction = 0

    def up(self):
        self.direction = -1

    def down(self):
        self.direction = 1

    def update(self):
        # a lot of this could probably be done once...ya turd
        if self.direction != 0:
            self.rect.move_ip(0, self.speed * self.direction)
            self.direction = 0
            self.dirty = True


class AutoPaddle(Paddle):

    def __init__(self, top, left):
        super().__init__(top, left)
        self.direction = random.choice((-1, 1))
        self.speed = 0

    def should_change_direction(self):
        return random.random() >= .99

    def update(self):
        self.speed = random.uniform(0, PADDLE_MAX_SPEED)
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
    pygame.display.set_caption('Pong')
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
        clock.tick(FPS)

    pygame.quit()


if __name__ == '__main__':
    main()
