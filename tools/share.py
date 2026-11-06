"""Compatibility entry point: social cards are now built with real episode pages.

Use tools/build_pages.py for new integrations. --all and --front remain accepted;
all published episode pages and cards are always generated together.
"""
import argparse
from pathlib import Path
from build_pages import build

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path, nargs='?', default=Path(__file__).resolve().parents[1])
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--front', action='store_true')
    args = parser.parse_args()
    build(args.root.resolve())
