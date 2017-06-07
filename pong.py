#!/usr/bin/env python3
"""
Pong in Pygame (written against Python 3.5)
"""

import argparse
import math
import sys
from collections import OrderedDict
from collections import namedtuple
from textwrap import dedent

import pygame
from pygame import locals as consts


global DEBUG
DEBUG_PATH_COLOR = (128, 0, 0,)

# Ye olde data structures
Sides = namedtuple('Sides', ['top', 'right', 'bottom', 'left'])
Corners = namedtuple('Corners',
                     ['topleft', 'topright', 'bottomright', 'bottomleft'])
Point = namedtuple('Point', ['x', 'y'])
Color = namedtuple('Color', ['r', 'g', 'b'])
Line = namedtuple('Line', ['slope', 'intercept'])

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
PADDLE_MIN_SPEED = 20 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_MAX_SPEED = 40 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_SPEED_INCR = 2 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_SPEED_DECR = 6 * BASE_FPS / FRAMES_PER_SECOND
PADDLE_HEIGHT = 120
PADDLE_WIDTH = 10
PADDLE_COLOR = Color(r=127, g=216, b=127)
PADDLE_DOWN_DIR = 1
PADDLE_UP_DIR = -1

# Sauce constants
SAUCE_MULTIPLIER = 30
SAUCE_MAX = SAUCE_MULTIPLIER // 2
SAUCE_MIN = -SAUCE_MAX

# Font constants
FONT = pygame.font.get_default_font()
TITLE_FONT_SIZE = 72
FONT_SIZE = 36
FONT_COLOR = Color(r=127, g=216, b=127)

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

    def dispatch(self, keys_pressed):
        for key, action in self.key_map.items():
            if keys_pressed[key]:
                self.actions.get(action, lambda: None)()


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

    def draw(self, surface):
        self.rect.draw(surface)


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


def is_quit_event(e):
    return (
        e.type == consts.QUIT or
        (e.type == consts.KEYDOWN and e.key == consts.K_ESCAPE)
    )


def pause_loop(screen):
    PAUSE_FPS = 10
    clock = pygame.time.Clock()
    font = pygame.font.Font(FONT, TITLE_FONT_SIZE)
    top = 200
    left = SCREEN_WIDTH // 2 - font.size("PAUSED")[0] // 2
    text = font.render("PAUSED", True, FONT_COLOR)
    text_rect = text.get_rect()
    text_rect.top = top
    text_rect.left = left
    screen.blit(text, text_rect)
    pygame.display.flip()
    clock.tick(PAUSE_FPS)
    while True:
        for e in pygame.event.get():
            if e.type == consts.KEYDOWN and e.key in [consts.K_p, 'p']:
                return
        clock.tick(PAUSE_FPS)


def menu_loop(screen):
    return 1


def game_loop(screen):
    screen_rect = Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    background = pygame.Surface(screen.get_size())
    background.fill(BACKGROUND_COLOR)
    screen.blit(background, (0, 0))

    num_players = menu_loop(screen)

    paddle1 = Paddle(100, 50)
    paddle2 = Paddle(screen_rect.width - 110, 50)
    human = Player(PLAYER1_KEY_MAP, paddle1)
    computer = MercilessAutomaton(paddle2)
    ball = Ball()
    game_objects = (paddle1, paddle2, ball,)
    clock = pygame.time.Clock()

    while True:
        for e in pygame.event.get():
            if is_quit_event(e):
                pygame.quit()
                sys.exit()
            elif e.type == consts.KEYDOWN and e.key == consts.K_p:
                pause_loop(screen)

        keys = pygame.key.get_pressed()

        if DEBUG and keys[consts.K_d]:
            import pdb; pdb.set_trace()  # noqa

        human.dispatch(keys)
        computer.play(ball)
        ball.handle_screen_edges(screen_rect)
        ball.handle_paddle_collision(paddle1)
        ball.handle_paddle_collision(paddle2)
        for fella in game_objects:
            fella.update()

        screen.blit(background, (0, 0))
        for fella in game_objects:
            fella.draw(screen)

        if DEBUG and len(computer.prediction.points) > 1:
            computer.prediction.draw(screen)

        pygame.display.flip()
        clock.tick(FRAMES_PER_SECOND)


def main():
    pygame.init()
    pygame.display.set_caption('pong')
    pygame.mouse.set_visible(False)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_loop(screen)
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
