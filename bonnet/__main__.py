#!/usr/bin/env python3
import os
from .cli import cli

def main():
    # Check if we're in completion mode
    complete_var = os.environ.get('_BONNET_COMPLETE')
    if complete_var:
        # Use Click's built-in completion
        cli.main(complete_var='_BONNET_COMPLETE')
    else:
        cli()

if __name__ == "__main__":
    main()