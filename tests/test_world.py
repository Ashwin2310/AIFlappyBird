import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from flappy.ai import load_config  # noqa: E402
from flappy.sprites import Bird, Images  # noqa: E402
from flappy.world import World  # noqa: E402

pygame.init()
pygame.display.set_mode((1, 1))


def test_birds_that_never_flap_fall_and_crash():
    world = World(3, rng=random.Random(1))
    for _ in range(200):
        if not world.alive:
            break
        world.step(lambda i, inputs: False)
    assert not world.alive
    assert all(f < 10 for f in world.fitness.values())


def test_crashed_birds_are_all_removed_in_the_same_frame():
    world = World(5, rng=random.Random(2))
    for bird in world.birds.values():
        bird.y = 2000  # everyone below the floor
    world.step(lambda i, inputs: False)
    assert world.birds == {}  # none skipped while removing


def test_jump_moves_bird_up():
    Images.ensure_loaded()
    bird = Bird(230, 350)
    bird.jump()
    bird.move()
    assert bird.y < 350 and bird.tilt == Bird.MAX_ROTATION


def test_inputs_are_three_numbers_and_config_loads():
    world = World(1, rng=random.Random(3))
    assert len(world.sense(world.birds[0])) == 3
    assert load_config().genome_config.num_inputs == 3
