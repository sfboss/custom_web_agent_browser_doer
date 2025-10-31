#!/bin/bash
# Print directory tree (uses tree if available, otherwise Python fallback)

if command -v tree &> /dev/null; then
    # Use tree command if available
    tree "$@"
else
    # Python fallback
    python3 - "$@" <<'PYTHON'
import os
import sys
from pathlib import Path

def print_tree(directory, prefix='', max_depth=3, current_depth=0):
    """Print directory tree."""
    if current_depth >= max_depth:
        return
    
    try:
        entries = sorted(Path(directory).iterdir(), key=lambda x: (not x.is_dir(), x.name))
    except PermissionError:
        return
    
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        current = '└── ' if is_last else '├── '
        print(f'{prefix}{current}{entry.name}')
        
        if entry.is_dir() and not entry.name.startswith('.'):
            extension = '    ' if is_last else '│   '
            print_tree(entry, prefix + extension, max_depth, current_depth + 1)

if __name__ == '__main__':
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(directory)
    print_tree(directory)
PYTHON
fi
