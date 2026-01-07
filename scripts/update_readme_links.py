#!/usr/bin/env python3
"""
Updates README.md documentation links to use specific submodule commit hashes.
Run automatically via pre-commit hook or manually when submodules are updated.
"""

import re
import subprocess
import sys
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def run_command(cmd: list[str], cwd: str | None = None) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
        return ""


def parse_gitmodules() -> dict[str, str]:
    """Parse .gitmodules to get submodule paths and URLs."""
    gitmodules_path = Path(".gitmodules")
    if not gitmodules_path.exists():
        print("Error: .gitmodules not found", file=sys.stderr)
        return {}

    submodules = {}
    current_path = None

    with open(gitmodules_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("[submodule"):
                current_path = None
            elif line.startswith("path ="):
                current_path = line.split("=", 1)[1].strip()
            elif line.startswith("url =") and current_path:
                url = line.split("=", 1)[1].strip()
                submodules[current_path] = url

    return submodules


def get_submodule_commit(submodule_path: str) -> str:
    """Get the commit hash that the parent repo is tracking for a submodule."""
    # Use git ls-tree to get the commit hash that the parent repo tracks
    output = run_command(["git", "ls-tree", "HEAD", submodule_path])
    if output:
        # Format: <mode> <type> <hash>\t<path>
        parts = output.split()
        if len(parts) >= 3:
            return parts[2]  # The commit hash
    return ""


def github_url_to_blob(repo_url: str, commit_hash: str, file_path: str = "README.md") -> str:
    """Convert GitHub repo URL to a blob URL for a specific commit."""
    # Remove .git suffix if present
    repo_url = repo_url.rstrip("/").removesuffix(".git")
    return f"{repo_url}/blob/{commit_hash}/{file_path}"


def extract_repo_url(link: str) -> str | None:
    """Extract the base repo URL from a GitHub blob link."""
    # Match pattern: https://github.com/USER/REPO/blob/BRANCH_OR_HASH/FILE
    match = re.match(r"(https://github\.com/[^/]+/[^/]+)/blob/[^/]+/(.+)", link)
    if match:
        return match.group(1), match.group(2)  # repo_url, file_path
    return None, None


def update_readme() -> bool:
    """Update README.md with commit-specific GitHub links. Returns True if changes were made."""
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("Error: README.md not found", file=sys.stderr)
        return False

    # Get submodule info
    submodules = parse_gitmodules()
    if not submodules:
        print("No submodules found in .gitmodules", file=sys.stderr)
        return False

    # Build mapping of repo URLs to commit hashes
    url_to_commit = {}
    for path, url in submodules.items():
        commit = get_submodule_commit(path)
        if commit:
            # Normalize URL for comparison
            normalized_url = url.rstrip("/").removesuffix(".git")
            url_to_commit[normalized_url] = commit
            print(f"✓ {path}: {commit}")
        else:
            print(f"⚠ Warning: Could not get commit for {path}", file=sys.stderr)

    # Read README
    with open(readme_path) as f:
        original_content = f.read()

    content = original_content

    # Update all GitHub blob links to use commit hashes
    # Pattern: https://github.com/USER/REPO/blob/BRANCH_OR_HASH/FILE
    def replace_link(match):
        full_link = match.group(0)
        repo_url, file_path = extract_repo_url(full_link)

        if repo_url and repo_url in url_to_commit:
            commit = url_to_commit[repo_url]
            new_link = github_url_to_blob(repo_url, commit, file_path)
            return new_link

        return full_link

    # Find and replace all GitHub blob links
    content = re.sub(
        r"https://github\.com/[^/]+/[^/]+/blob/[^/\s\)]+/[^\s\)]+",
        replace_link,
        content
    )

    # Check if changes were made
    if content == original_content:
        print("\n✓ README.md already up to date")
        return False

    # Write updated README
    with open(readme_path, "w") as f:
        f.write(content)

    # Stage the updated README
    run_command(["git", "add", "README.md"])

    print("\n✓ README.md updated with commit-specific links and staged")
    return True


if __name__ == "__main__":
    try:
        update_readme()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)