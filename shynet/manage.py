#!/usr/bin/env python3
"""Shynet's command-line utility for administrative tasks."""
import sys

from flask.cli import FlaskGroup

from shynet.app import create_app

cli = FlaskGroup(create_app=create_app)


def main():
    cli.main(args=sys.argv[1:])


if __name__ == "__main__":
    main()
