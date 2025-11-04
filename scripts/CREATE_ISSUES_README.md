# Create Issues from TODO.md

This script automates the creation of GitHub issues from unchecked items in the `docs/TODO.md` file.

## Prerequisites

- GitHub CLI (`gh`) must be installed and authenticated
- You must have write access to the repository

## Usage

### Preview Issues (Dry Run)

To see what issues would be created without actually creating them:

```bash
python scripts/create_issues_from_todo.py --dry-run
```

### Create Issues

To actually create the issues in GitHub:

```bash
python scripts/create_issues_from_todo.py
```

### Create Issues with Labels

You can add labels to all created issues:

```bash
python scripts/create_issues_from_todo.py --label "enhancement" --label "from-todo"
```

### Custom TODO File

By default, the script reads from `docs/TODO.md`. To use a different file:

```bash
python scripts/create_issues_from_todo.py --todo-file path/to/your/TODO.md
```

## How It Works

1. The script parses the TODO.md file and finds all unchecked items (lines starting with `- [ ]`)
2. For each unchecked item, it creates a GitHub issue with:
   - **Title**: The task description
   - **Body**: The task description, line number reference, and automatic attribution
   - **Labels**: Any labels specified via command line

3. Issues are created using the `gh` CLI tool

## Example

Given this TODO.md content:

```markdown
# Current Tasks

- [x] Completed task
- [ ] Sort and filter professors
- [ ] Jobs UI Page for Admin
```

Running the script will create 2 issues:
- Issue 1: "Sort and filter professors"
- Issue 2: "Jobs UI Page for Admin"

Each issue will include a reference to the line number in TODO.md where it originated.

## Notes

- The script skips items that are already checked (marked with `[x]`)
- Each issue references its source line number in TODO.md
- Issues include automatic attribution noting they were created from TODO.md
- Use `--dry-run` to preview before creating actual issues
