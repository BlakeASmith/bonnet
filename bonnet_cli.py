#!/usr/bin/env python3
import sys
from bonnet.cli import BonnetCLI

def main():
    cli = BonnetCLI()
    cli.run(sys.argv[1:])

if __name__ == "__main__":
    main()