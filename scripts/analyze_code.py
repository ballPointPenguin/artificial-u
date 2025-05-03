#!/usr/bin/env python3

import ast
import os
import re


def count_lines(file_path):
    """Count non-empty lines in a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return len([line for line in f if line.strip()])


def analyze_file(file_path):
    """Analyze a Python file for function definitions and their sizes."""
    file_size = os.path.getsize(file_path)
    line_count = count_lines(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse Python code
        tree = ast.parse(content)

        # Extract function info
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_name = node.name
                start_line = node.lineno

                # Find end line by going through source code lines
                end_line = start_line
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                indent_level = len(re.match(r"^\s*", lines[start_line - 1]).group())
                current_line = start_line

                while current_line < len(lines):
                    if current_line >= start_line and (
                        current_line == len(lines) - 1
                        or (
                            re.match(r"^\s*", lines[current_line]).group()
                            and len(re.match(r"^\s*", lines[current_line]).group()) <= indent_level
                            and lines[current_line].strip()
                        )
                    ):
                        break
                    end_line = current_line
                    current_line += 1

                func_size = end_line - start_line + 1
                functions.append(
                    {
                        "name": func_name,
                        "size": func_size,
                        "start_line": start_line,
                        "end_line": end_line,
                    }
                )

        return {
            "file_path": file_path,
            "file_size": file_size,
            "line_count": line_count,
            "functions": functions,
        }
    except Exception as e:
        return {
            "file_path": file_path,
            "file_size": file_size,
            "line_count": line_count,
            "error": str(e),
            "functions": [],
        }


def find_python_files(directory):
    """Find all Python files in directory and subdirectories."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    target_dir = "artificial_u"

    print(f"Analyzing Python files in {target_dir}...")
    python_files = find_python_files(target_dir)

    # File statistics
    print(f"\nFound {len(python_files)} Python files")

    file_stats = []
    for py_file in python_files:
        stats = analyze_file(py_file)
        file_stats.append(stats)

    # Sort files by size
    sorted_by_size = sorted(file_stats, key=lambda x: x["file_size"], reverse=True)

    print("\n=== Files by Size ===")
    for i, stats in enumerate(sorted_by_size[:10], 1):
        readable_size = (
            f"{stats['file_size'] / 1024:.1f} KB"
            if stats["file_size"] >= 1024
            else f"{stats['file_size']} bytes"
        )
        print(f"{i}. {stats['file_path']} - {readable_size}, {stats['line_count']} lines")

    # Collect all functions
    all_functions = []
    for stats in file_stats:
        for func in stats["functions"]:
            all_functions.append(
                {
                    "file": stats["file_path"],
                    "name": func["name"],
                    "size": func["size"],
                    "start_line": func["start_line"],
                    "end_line": func["end_line"],
                }
            )

    # Sort functions by size
    sorted_functions = sorted(all_functions, key=lambda x: x["size"], reverse=True)

    print("\n=== Longest Functions ===")
    for i, func in enumerate(sorted_functions[:20], 1):
        print(
            f"{i}. {func['file']}:{func['name']} - {func['size']} lines (L{func['start_line']}-{func['end_line']})"
        )


if __name__ == "__main__":
    main()
