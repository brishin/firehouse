#!/usr/bin/env python

import argparse
import sys

from commands.autobranch import Autobranch
from commands.submit import Submit

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Commands")
    Autobranch().register_command(subparsers)

    Submit().register_command(subparsers)

    args = parser.parse_args(None if sys.argv[1:] else ["--help"])
    args.handler(args)
