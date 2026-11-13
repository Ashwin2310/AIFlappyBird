"""Game objects: the bird, the pipes and the scrolling ground."""
from __future__ import annotations

import random
from pathlib import Path

import pygame

ASSETS = Path(__file__).resolve().parent.parent / "imgs"
WIN_WIDTH, WIN_HEIGHT = 500, 800
FLOOR_Y = 730
SCROLL_SPEED = 5


def load(name: str) -> pygame.Surface:
    return pygame.transform.scale2x(pygame.image.load(str(ASSETS / name)))


class Images:
    """Loaded lazily, after pygame.display is set up (convert_alpha needs a display)."""
    bird: list[pygame.Surface] = []
    pipe: pygame.Surface | None = None
    base: pygame.Surface | None = None
    background: pygame.Surface | None = None

    @classmethod
    def ensure_loaded(cls) -> None:
        if cls.pipe is None:
            cls.bird = [load(f"bird{i}.png") for i in (1, 2, 3)]
            cls.pipe, cls.base, cls.background = load("pipe.png"), load("base.png"), load("bg.png")


class Bird:
    MAX_ROTATION = 25
    ROTATION_SPEED = 20
    ANIMATION_TIME = 5
    JUMP_VELOCITY = -10.5
    GRAVITY = 1.5
    TERMINAL_DROP = 16

    def __init__(self, x: int, y: int) -> None:
        self.x, self.y = x, y
        self.tilt = 0.0
        self.ticks = 0
        self.velocity = 0.0
        self.jump_height = y
        self.frame = 0
        self.img = Images.bird[0]

    def jump(self) -> None:
        self.velocity = self.JUMP_VELOCITY
        self.ticks = 0
        self.jump_height = self.y

    def move(self) -> None:
        """Projectile motion since the last jump, capped at terminal velocity."""
        self.ticks += 1
        drop = min(self.velocity * self.ticks + self.GRAVITY * self.ticks ** 2, self.TERMINAL_DROP)
        if drop < 0:
            drop -= 2  # a little extra lift on the way up
        self.y += drop
        if drop < 0 or self.y < self.jump_height + 50:
            self.tilt = self.MAX_ROTATION
        elif self.tilt > -90:
            self.tilt -= self.ROTATION_SPEED

    def _animation_frame(self) -> pygame.Surface:
        if self.tilt <= -80:
            return Images.bird[1]  # nose-diving: wings level
        self.frame = (self.frame + 1) % (self.ANIMATION_TIME * 4)
        cycle = (0, 1, 2, 1)
        return Images.bird[cycle[self.frame // self.ANIMATION_TIME]]

    def draw(self, win: pygame.Surface) -> None:
        self.img = self._animation_frame()
        rotated = pygame.transform.rotate(self.img, self.tilt)
        centre = self.img.get_rect(topleft=(self.x, self.y)).center
        win.blit(rotated, rotated.get_rect(center=centre).topleft)

    def mask(self) -> pygame.mask.Mask:
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200

    def __init__(self, x: int, rng: random.Random | None = None) -> None:
        self.x = x
        self.top_img = pygame.transform.flip(Images.pipe, False, True)
        self.bottom_img = Images.pipe
        self.height = (rng or random).randrange(40, 450)
        self.top = self.height - self.top_img.get_height()
        self.bottom = self.height + self.GAP
        self.passed = False

    @property
    def width(self) -> int:
        return self.top_img.get_width()

    def move(self) -> None:
        self.x -= SCROLL_SPEED

    def draw(self, win: pygame.Surface) -> None:
        win.blit(self.top_img, (self.x, self.top))
        win.blit(self.bottom_img, (self.x, self.bottom))

    def collides_with(self, bird: Bird) -> bool:
        """Pixel-perfect collision using masks."""
        bird_mask = bird.mask()
        top = bird_mask.overlap(pygame.mask.from_surface(self.top_img), (self.x - bird.x, self.top - round(bird.y)))
        bottom = bird_mask.overlap(pygame.mask.from_surface(self.bottom_img), (self.x - bird.x, self.bottom - round(bird.y)))
        return bool(top or bottom)


class Ground:
    """Two copies of the ground image leap-frog each other to scroll forever."""

    def __init__(self, y: int) -> None:
        self.y = y
        self.width = Images.base.get_width()
        self.x1, self.x2 = 0, self.width

    def move(self) -> None:
        self.x1 -= SCROLL_SPEED
        self.x2 -= SCROLL_SPEED
        if self.x1 + self.width < 0:
            self.x1 = self.x2 + self.width
        if self.x2 + self.width < 0:
            self.x2 = self.x1 + self.width

    def draw(self, win: pygame.Surface) -> None:
        win.blit(Images.base, (self.x1, self.y))
        win.blit(Images.base, (self.x2, self.y))
