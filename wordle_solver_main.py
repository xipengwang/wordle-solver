#!/usr/bin/env python3
import argparse
import os
import sys
import json
import logging

from wordle_solver import WordleSolver

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('word_list', type=str, help="A json array contains all words")
    parser.add_argument('--mode', choices=["interaction", "simulate"], default="interaction")
    args = parser.parse_args()

    if args.word_list is not None:
        assert os.path.exists(args.word_list)
        with open(args.word_list, 'r') as f:
            words = json.load(f)
    else:
        words = ["hello", "world"]
    if args.mode == 'interaction':
        wordle_solver = WordleSolver(words)
        wordle_solver.interactive_solve()
    elif args.mode == 'simulate':
        wordle_solver = WordleSolver(words, logging_level=logging.ERROR)
        wordle_solver.test_performance()
    return 0

if __name__ == '__main__':
    sys.exit(main())
