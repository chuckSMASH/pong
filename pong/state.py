'''
Model menu mode, game mode, pause mode etc as a state machine
'''
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys
from abc import ABCMeta
from abc import abstractmethod
from types import SimpleNamespace

import pygame
import six
from pygame import locals as consts

from .game import BACKGROUND_COLOR
from .game import FRAMES_PER_SECOND
from .game import PADDLE_WIDTH
from .game import PLAYER1_KEY_MAP
# from .game import PLAYER2_KEY_MAP
from .game import SCREEN_HEIGHT
from .game import SCREEN_WIDTH
from .game import Ball
from .game import Color
from .game import MercilessAutomaton
from .game import Paddle
from .game import Player
from .geometry import Rect


DEBUG = False  # fixme

# Font constants
FONT = pygame.font.get_default_font()
FONT_COLOR = Color(r=127, g=216, b=127)
PAUSE_FONT_SIZE = 72


class State(six.with_metaclass(ABCMeta, object)):

    @abstractmethod
    def run(self, game):
        raise NotImplementedError

    def is_quit_event(self, e):
        return (
            e.type == consts.QUIT or
            (e.type == consts.KEYDOWN and e.key == consts.K_ESCAPE)
        )

    def is_pause_event(self, e):
        return e.type == consts.KEYDOWN and e.key == consts.K_p


class Menu(State):

    def run(self, game):
        pass


class Playing(State):

    def run(self, game):
        screen_rect = Rect(0, 0, game.screen_width, game.screen_height)
        background = game.background
        screen = game.screen
        fps = game.fps
        clock = game.clock
        screen.blit(game.background, (0, 0))
        players = game.players
        ball = game.ball
        paddles = [p.paddle for p in players]
        sprites = paddles + [ball]
        predictions = [p.prediction for p in players if not p.is_human]

        while True:
            for e in pygame.event.get():
                if self.is_quit_event(e):
                    return None
                if self.is_pause_event(e):
                    return game.states.paused

            keys = pygame.key.get_pressed()

            if game.debug and keys[consts.K_d]:
                import pdb; pdb.set_trace()  # noqa

            ball.handle_screen_edges(screen_rect)
            for player in players:
                if player.is_human:
                    player.dispatch(keys)
                else:
                    player.play(ball)
                ball.handle_paddle_collision(player.paddle)
                screen.blit(background, (0, 0))
            for sprite in sprites:
                sprite.update()
                sprite.draw(screen)

            if game.debug:
                for prediction in predictions:
                    if len(prediction.points) > 1:
                        prediction.draw(screen)

            pygame.display.flip()
            clock.tick(fps)


class Paused(State):

    def run(self, game):
        clock = game.clock
        font = game.pause_font
        fps = 10  # cough constant cough
        top = 200  # ditto
        left = game.screen_width // 2 - font.size("PAUSED")[0] // 2
        text = font.render("PAUSED", True, game.font_color)
        text_rect = text.get_rect()
        text_rect.top = top
        text_rect.left = left
        game.screen.blit(text, text_rect)
        pygame.display.flip()
        clock.tick(fps)
        while True:
            for e in pygame.event.get():
                if self.is_quit_event(e):
                    return None
                if self.is_pause_event(e):
                    return game.states.playing
            clock.tick(fps)


class Game(object):

    def __init__(self):
        pygame.init()
        pygame.display.set_caption('pong')
        pygame.mouse.set_visible(False)

        self.states = SimpleNamespace()
        self.states.menu = Menu()
        self.states.playing = Playing()
        self.states.paused = Paused()

        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fps = FRAMES_PER_SECOND
        self.clock = pygame.time.Clock()
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill(BACKGROUND_COLOR)
        self.screen.blit(self.background, (0, 0))

        paddle1 = Paddle(100, 50)
        paddle2 = Paddle(SCREEN_WIDTH - 100 - PADDLE_WIDTH,  50)
        self.players = [
            Player(PLAYER1_KEY_MAP, paddle1),
            MercilessAutomaton(paddle2),
        ]
        self.ball = Ball()

        self.font_color = FONT_COLOR
        self.pause_font = pygame.font.Font(FONT, PAUSE_FONT_SIZE)

    def run(self, debug=False):
        self.debug = debug
        state = self.states.playing.run(self)
        while state is not None:
            state = state.run(self)
        pygame.quit()
        sys.exit()
