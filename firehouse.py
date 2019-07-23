#!/usr/bin/env python

import argparse

from commands.autobranch import Autobranch

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="Commands")
    Autobranch().register_command(subparsers)

    args = parser.parse_args()
    args.handler(args)
