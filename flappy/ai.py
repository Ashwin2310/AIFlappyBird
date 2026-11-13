"""NEAT training loop and replay of the best saved bird."""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import neat
import pygame

from .sprites import WIN_HEIGHT, WIN_WIDTH
from .world import World

FPS = 30
FLAP_THRESHOLD = 0.5
CONFIG_PATH = Path(__file__).resolve().parent.parent / "NEAT-config.txt"
WINNER_PATH = Path("best_bird.pkl")


@dataclass
class Display:
    win: pygame.Surface
    font: pygame.font.Font
    clock: pygame.time.Clock
    fast: bool = False


class QuitRequested(Exception):
    """The player closed the window."""


def open_display(fast: bool) -> Display:
    pygame.init()
    pygame.display.set_caption("AI Flappy Bird (NEAT)")
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    return Display(win, pygame.font.SysFont("arialrounded,arial", 30, bold=True), pygame.time.Clock(), fast)


def load_config(path: Path = CONFIG_PATH) -> neat.Config:
    return neat.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                       neat.DefaultStagnation, str(path))


def play_round(nets: list, display: Display, generation: int, score_limit: int | None = None) -> World:
    world = World(len(nets))
    while world.alive and (score_limit is None or world.score < score_limit):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                raise QuitRequested
        world.step(lambda i, inputs: nets[i].activate(inputs)[0] > FLAP_THRESHOLD)
        world.draw(display.win, display.font, generation)
        pygame.display.flip()
        if not display.fast:
            display.clock.tick(FPS)
    return world


def train(generations: int, fast: bool, score_limit: int) -> None:
    config = load_config()
    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    population.add_reporter(neat.StatisticsReporter())
    display = open_display(fast)

    def evaluate(genomes, cfg) -> None:
        nets = [neat.nn.FeedForwardNetwork.create(g, cfg) for _, g in genomes]
        world = play_round(nets, display, population.generation + 1, score_limit)
        for i, (_, genome) in enumerate(genomes):
            genome.fitness = world.fitness[i]

    try:
        winner = population.run(evaluate, generations)
    except QuitRequested:
        print("Training stopped.")
        return
    finally:
        pygame.quit()
    WINNER_PATH.write_bytes(pickle.dumps(winner))
    print(f"Best bird saved to {WINNER_PATH}. Watch it with: python main.py replay")


def replay(path: Path = WINNER_PATH) -> None:
    if not path.exists():
        raise SystemExit(f"No saved bird at {path}. Train one first: python main.py train")
    genome = pickle.loads(path.read_bytes())
    net = neat.nn.FeedForwardNetwork.create(genome, load_config())
    display = open_display(fast=False)
    try:
        world = play_round([net], display, generation=0)
        print(f"Final score: {world.score}")
    except QuitRequested:
        pass
    finally:
        pygame.quit()
