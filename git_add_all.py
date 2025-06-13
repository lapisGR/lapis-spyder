#!/usr/bin/env python3
"""Add all changes to git including submodules."""

import subprocess
import os

def run_command(cmd):
    """Run a command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

# Change to project directory
os.chdir('/Users/saisur/Desktop/lapis/lapisResearch/lapis-llmt_spyder')

print("Current directory:", os.getcwd())

# Check git status
print("\n=== Git Status ===")
stdout, stderr, code = run_command("git status --porcelain")
if stdout:
    print(stdout)
else:
    print("No changes detected")

# Add all changes
print("\n=== Adding all changes ===")
stdout, stderr, code = run_command("git add -A")
if code == 0:
    print("✓ All changes added")
else:
    print(f"Error: {stderr}")

# Check for submodules
print("\n=== Checking submodules ===")
if os.path.exists('.gitmodules'):
    print("Submodules found:")
    stdout, stderr, code = run_command("git submodule status")
    print(stdout)
    
    # Update submodule references
    stdout, stderr, code = run_command("git submodule update --init --recursive")
    if code == 0:
        print("✓ Submodules updated")
else:
    print("No submodules found")

# Show what will be committed
print("\n=== Changes to be committed ===")
stdout, stderr, code = run_command("git status --short")
print(stdout)

print("\n✅ All changes have been staged for commit")
print("To commit, run: git commit -m 'Your message here'")