#!/usr/bin/env python3
import os
import sys
import click

@click.group()
def cli():
    """Test CLI with completion"""
    pass

@cli.command()
def cmd1():
    """First command"""
    click.echo("cmd1")

@cli.command()
def cmd2():
    """Second command"""
    click.echo("cmd2")

if __name__ == "__main__":
    # Check if we're in completion mode
    complete_var = os.environ.get('_TEST_CLI_COMPLETE')
    if complete_var:
        print(f"Completion mode: {complete_var}")
        print("Available commands: cmd1 cmd2")
        sys.exit(0)
    
    cli()