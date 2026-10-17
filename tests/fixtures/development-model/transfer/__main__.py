"""Run from the model project root with python -m transfer."""

import argparse

from .model import TransferModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=41)
    args = parser.parse_args()
    model = TransferModel(seed=args.seed)
    for _ in range(args.steps):
        model.step()
    print(model.export())


if __name__ == "__main__":
    main()
