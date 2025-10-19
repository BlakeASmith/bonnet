#!/usr/bin/env python3
"""
Setup script for bonnet shell completion.
This script helps users set up shell completion for the bonnet CLI.
"""
import os
import sys
import subprocess
import click
from pathlib import Path


def get_shell():
    """Detect the current shell"""
    shell = os.environ.get('SHELL', '')
    if 'bash' in shell:
        return 'bash'
    elif 'zsh' in shell:
        return 'zsh'
    elif 'fish' in shell:
        return 'fish'
    else:
        return 'bash'  # Default to bash


def setup_bash_completion():
    """Setup bash completion"""
    bashrc_path = Path.home() / '.bashrc'
    completion_file = Path.home() / '.bonnet-complete.bash'
    
    # Generate completion script
    try:
        result = subprocess.run(['bonnet', 'completion', '--shell', 'bash'], 
                              capture_output=True, text=True, check=True)
        completion_file.write_text(result.stdout)
        print(f"✓ Generated completion script: {completion_file}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating completion script: {e}")
        return False
    
    # Add to .bashrc
    bashrc_content = bashrc_path.read_text() if bashrc_path.exists() else ""
    
    # Check if already added
    if 'bonnet-complete.bash' in bashrc_content:
        print("✓ Bash completion already configured in ~/.bashrc")
        return True
    
    # Add completion setup
    setup_line = f"\n# Bonnet CLI completion\n. {completion_file}\n"
    bashrc_path.write_text(bashrc_content + setup_line)
    print(f"✓ Added completion setup to {bashrc_path}")
    return True


def setup_zsh_completion():
    """Setup zsh completion"""
    zshrc_path = Path.home() / '.zshrc'
    completion_file = Path.home() / '.bonnet-complete.zsh'
    
    # Generate completion script
    try:
        result = subprocess.run(['bonnet', 'completion', '--shell', 'zsh'], 
                              capture_output=True, text=True, check=True)
        completion_file.write_text(result.stdout)
        print(f"✓ Generated completion script: {completion_file}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating completion script: {e}")
        return False
    
    # Add to .zshrc
    zshrc_content = zshrc_path.read_text() if zshrc_path.exists() else ""
    
    # Check if already added
    if 'bonnet-complete.zsh' in zshrc_content:
        print("✓ Zsh completion already configured in ~/.zshrc")
        return True
    
    # Add completion setup
    setup_line = f"\n# Bonnet CLI completion\n. {completion_file}\n"
    zshrc_path.write_text(zshrc_content + setup_line)
    print(f"✓ Added completion setup to {zshrc_path}")
    return True


def setup_fish_completion():
    """Setup fish completion"""
    fish_completions_dir = Path.home() / '.config' / 'fish' / 'completions'
    completion_file = fish_completions_dir / 'bonnet.fish'
    
    # Create completions directory
    fish_completions_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate completion script
    try:
        result = subprocess.run(['bonnet', 'completion', '--shell', 'fish'], 
                              capture_output=True, text=True, check=True)
        completion_file.write_text(result.stdout)
        print(f"✓ Generated completion script: {completion_file}")
        print("✓ Fish will automatically load completions from this directory")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating completion script: {e}")
        return False


@click.command()
@click.option('--shell', type=click.Choice(['bash', 'zsh', 'fish', 'auto'], case_sensitive=False),
              default='auto', help='Shell type to setup completion for')
@click.option('--force', is_flag=True, help='Force reconfiguration even if already set up')
def main(shell, force):
    """Setup shell completion for bonnet CLI"""
    
    if shell == 'auto':
        shell = get_shell()
        print(f"Detected shell: {shell}")
    
    print(f"Setting up {shell} completion for bonnet...")
    
    success = False
    if shell == 'bash':
        success = setup_bash_completion()
    elif shell == 'zsh':
        success = setup_zsh_completion()
    elif shell == 'fish':
        success = setup_fish_completion()
    else:
        print(f"Unsupported shell: {shell}")
        sys.exit(1)
    
    if success:
        print("\n✓ Shell completion setup complete!")
        print("\nTo activate completion:")
        if shell == 'bash':
            print("  source ~/.bashrc")
        elif shell == 'zsh':
            print("  source ~/.zshrc")
        elif shell == 'fish':
            print("  # Fish will automatically load completions")
        print("\nTest completion by typing 'bonnet ' and pressing TAB")
    else:
        print("\n✗ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()