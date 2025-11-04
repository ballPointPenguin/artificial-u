#!/usr/bin/env python3
"""
Script to create GitHub issues from TODO.md file.

This script reads the docs/TODO.md file, extracts unchecked items,
and creates GitHub issues for each one using the GitHub CLI.

Usage:
    python scripts/create_issues_from_todo.py --dry-run  # Preview what would be created
    python scripts/create_issues_from_todo.py            # Actually create issues
    python scripts/create_issues_from_todo.py --label "enhancement" --label "todo"
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def parse_todo_file(file_path: Path) -> List[Tuple[str, int]]:
    """
    Parse TODO.md and extract unchecked items.

    Returns a list of tuples: (task_description, line_number)
    """
    unchecked_items = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}")
        sys.exit(1)

    for line_num, line in enumerate(lines, start=1):
        # Match lines with unchecked checkbox: - [ ] ...
        if re.match(r"^-\s*\[\s*\]\s+", line):
            # Extract the task description (everything after "- [ ] ")
            task = re.sub(r"^-\s*\[\s*\]\s+", "", line).strip()
            unchecked_items.append((task, line_num))

    return unchecked_items


def create_issue_title(task: str) -> str:
    """Create a concise issue title from the task description."""
    # Use the task as-is for the title
    return task


def create_issue_body(task: str, line_number: int) -> str:
    """Create the issue body with context."""
    body = f"""This task was extracted from `docs/TODO.md` (line {line_number}).

## Task
{task}

---
*This issue was automatically created from the TODO.md file.*
"""
    return body


def create_github_issue(title: str, body: str, labels: List[str], dry_run: bool = False) -> bool:
    """
    Create a GitHub issue using the gh CLI.

    Args:
        title: Issue title
        body: Issue body text
        labels: List of labels to apply
        dry_run: If True, just print what would be done

    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"\n{'='*80}")
        print(f"TITLE: {title}")
        print(f"LABELS: {', '.join(labels) if labels else 'None'}")
        print(f"{'='*80}")
        print(body)
        return True

    # Build the gh CLI command
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]

    # Add labels if provided
    for label in labels:
        cmd.extend(["--label", label])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Created issue: {title}")
        if result.stdout:
            print(f"  URL: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create issue: {title}")
        print(f"  Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed or not in PATH")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from TODO.md file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be created
  %(prog)s --dry-run
  
  # Create issues with labels
  %(prog)s --label enhancement --label todo
  
  # Create issues without any labels
  %(prog)s
        """,
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview issues without creating them"
    )

    parser.add_argument(
        "--label",
        action="append",
        dest="labels",
        default=[],
        help="Label to add to issues (can be specified multiple times)",
    )

    parser.add_argument(
        "--todo-file",
        type=Path,
        default=Path(__file__).parent.parent / "docs" / "TODO.md",
        help="Path to TODO.md file (default: docs/TODO.md)",
    )

    args = parser.parse_args()

    # Parse the TODO file
    print(f"Reading TODO items from: {args.todo_file}")
    unchecked_items = parse_todo_file(args.todo_file)

    if not unchecked_items:
        print("No unchecked items found in TODO.md")
        return 0

    print(f"Found {len(unchecked_items)} unchecked items")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No issues will be created")
    else:
        print("\n🚀 Creating GitHub issues...")

    # Create issues for each unchecked item
    success_count = 0
    for task, line_num in unchecked_items:
        title = create_issue_title(task)
        body = create_issue_body(task, line_num)

        if create_github_issue(title, body, args.labels, args.dry_run):
            success_count += 1

    # Summary
    print(f"\n{'='*80}")
    if args.dry_run:
        print(f"DRY RUN: Would create {success_count} issues")
    else:
        print(f"Successfully created {success_count}/{len(unchecked_items)} issues")

    return 0 if success_count == len(unchecked_items) else 1


if __name__ == "__main__":
    sys.exit(main())
