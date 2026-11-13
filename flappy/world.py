"""One round of the game for many birds at once, controlled by a decide() callback per bird."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

import pygame

from .sprites import FLOOR_Y, WIN_WIDTH, Bird, Ground, Images, Pipe

BIRD_START = (230, 350)
FIRST_PIPE_X = 600
SURVIVAL_REWARD = 0.1
PIPE_REWARD = 5.0
CRASH_PENALTY = 1.0

# decide(bird_index, inputs) -> True to flap
Decide = Callable[[int, tuple[float, float, float]], bool]


@dataclass
class World:
    population: int
    rng: random.Random = field(default_factory=random.Random)
    score: int = 0

    def __post_init__(self) -> None:
        Images.ensure_loaded()
        self.birds: dict[int, Bird] = {i: Bird(*BIRD_START) for i in range(self.population)}
        self.fitness: dict[int, float] = {i: 0.0 for i in range(self.population)}
        self.pipes = [Pipe(FIRST_PIPE_X, self.rng)]
        self.ground = Ground(FLOOR_Y)

    @property
    def alive(self) -> bool:
        return bool(self.birds)

    def _next_pipe(self) -> Pipe:
        bird_x = BIRD_START[0]
        if len(self.pipes) > 1 and bird_x > self.pipes[0].x + self.pipes[0].width:
            return self.pipes[1]
        return self.pipes[0]

    def sense(self, bird: Bird) -> tuple[float, float, float]:
        """Neural-network inputs: height, distance to the top pipe, distance to the bottom pipe."""
        pipe = self._next_pipe()
        return bird.y, abs(bird.y - pipe.height), abs(bird.y - pipe.bottom)

    def step(self, decide: Decide) -> None:
        """Advance one frame: think, move, score, and remove crashed birds."""
        for i, bird in self.birds.items():
            bird.move()
            self.fitness[i] += SURVIVAL_REWARD
            if decide(i, self.sense(bird)):
                bird.jump()

        crashed = {i for i, b in self.birds.items()
                   if b.y + b.img.get_height() >= FLOOR_Y or b.y < 0
                   or any(p.collides_with(b) for p in self.pipes)}
        for i in crashed:
            self.fitness[i] -= CRASH_PENALTY
        self.birds = {i: b for i, b in self.birds.items() if i not in crashed}

        passed_new_pipe = False
        for pipe in self.pipes:
            if not pipe.passed and pipe.x < BIRD_START[0]:
                pipe.passed = passed_new_pipe = True
            pipe.move()
        if passed_new_pipe:
            self.score += 1
            for i in self.birds:
                self.fitness[i] += PIPE_REWARD
            self.pipes.append(Pipe(FIRST_PIPE_X, self.rng))
        self.pipes = [p for p in self.pipes if p.x + p.width >= 0]
        self.ground.move()

    def draw(self, win: pygame.Surface, font: pygame.font.Font, generation: int) -> None:
        win.blit(Images.background, (0, 0))
        for pipe in self.pipes:
            pipe.draw(win)
        self.ground.draw(win)
        for bird in self.birds.values():
            bird.draw(win)
        labels = (f"Score: {self.score}", f"Gen: {generation}", f"Alive: {len(self.birds)}")
        for row, text in enumerate(labels):
            surface = font.render(text, True, (255, 255, 255))
            win.blit(surface, (WIN_WIDTH - 12 - surface.get_width(), 10 + row * 34) if row == 0 else (12, 10 + (row - 1) * 34))
