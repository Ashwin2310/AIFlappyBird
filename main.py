"""AI Flappy Bird.

  python main.py train [--generations 50] [--fast] [--score-limit 50]
  python main.py replay      # watch the best bird from the last training run
"""
import argparse

from flappy.ai import replay, train


def main() -> None:
    parser = argparse.ArgumentParser(description="Train birds to play Flappy Bird with NEAT.")
    sub = parser.add_subparsers(dest="command", required=True)
    t = sub.add_parser("train", help="evolve a population of birds")
    t.add_argument("--generations", type=int, default=50)
    t.add_argument("--fast", action="store_true", help="don't cap the frame rate")
    t.add_argument("--score-limit", type=int, default=50, help="end a generation once a bird scores this much")
    sub.add_parser("replay", help="watch the best saved bird")
    args = parser.parse_args()
    if args.command == "train":
        train(args.generations, args.fast, args.score_limit)
    else:
        replay()


if __name__ == "__main__":
    main()
