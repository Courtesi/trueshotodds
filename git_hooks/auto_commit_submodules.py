#!/usr/bin/env python3
"""
Automatically commits and pushes submodule changes before parent repo commit.
Run automatically via pre-commit hook.
"""

import subprocess
import sys
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def run_command(cmd: list[str], cwd: str | None = None, check: bool = True) -> tuple[str, str, int]:
    """Run a shell command and return stdout, stderr, and return code."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            cwd=cwd,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode


def get_submodules() -> list[str]:
    """Get list of submodule paths."""
    stdout, _, _ = run_command(["git", "config", "--file", ".gitmodules", "--get-regexp", "path"])
    if not stdout:
        return []

    submodules = []
    for line in stdout.split('\n'):
        if line:
            # Format: submodule.<name>.path <path>
            path = line.split()[-1]
            submodules.append(path)

    return submodules


def submodule_has_changes(submodule_path: str) -> bool:
    """Check if a submodule has uncommitted or unpushed changes."""
    if not Path(submodule_path).exists():
        return False

    # Check for uncommitted changes
    stdout, _, _ = run_command(["git", "status", "--porcelain"], cwd=submodule_path, check=False)
    if stdout:
        return True

    # Check for unpushed commits
    stdout, _, returncode = run_command(
        ["git", "rev-list", "@{u}..HEAD"],
        cwd=submodule_path,
        check=False
    )
    if returncode == 0 and stdout:
        return True

    return False


def get_parent_commit_message() -> str:
    """Try to get the commit message from COMMIT_EDITMSG if available."""
    commit_msg_file = Path(".git/COMMIT_EDITMSG")
    if commit_msg_file.exists():
        with open(commit_msg_file) as f:
            lines = f.readlines()
            # Get first non-comment line
            for line in lines:
                if line and not line.startswith('#'):
                    return line.strip()
    return ""


def commit_and_push_submodule(submodule_path: str, commit_message: str) -> bool:
    """Commit and push changes in a submodule. Returns True if successful."""
    print(f"\n📦 Processing {submodule_path}...")

    # Check if there are uncommitted changes
    stdout, _, _ = run_command(["git", "status", "--porcelain"], cwd=submodule_path, check=False)

    if stdout:
        print(f"   Staging changes in {submodule_path}...")
        # Stage all changes
        _, stderr, returncode = run_command(["git", "add", "-A"], cwd=submodule_path, check=False)
        if returncode != 0:
            print(f"   ✗ Failed to stage changes: {stderr}", file=sys.stderr)
            return False

        # Commit changes
        print(f"   Committing changes...")
        _, stderr, returncode = run_command(
            ["git", "commit", "-m", commit_message],
            cwd=submodule_path,
            check=False
        )
        if returncode != 0:
            print(f"   ✗ Failed to commit: {stderr}", file=sys.stderr)
            return False

        print(f"   ✓ Committed changes")
    else:
        print(f"   No uncommitted changes")

    # Check if there are commits to push
    stdout, _, returncode = run_command(
        ["git", "rev-list", "@{u}..HEAD"],
        cwd=submodule_path,
        check=False
    )

    if returncode == 0 and stdout:
        # There are unpushed commits
        print(f"   Pushing to remote...")
        _, stderr, returncode = run_command(
            ["git", "push"],
            cwd=submodule_path,
            check=False
        )
        if returncode != 0:
            print(f"   ✗ Failed to push: {stderr}", file=sys.stderr)
            return False

        print(f"   ✓ Pushed to remote")
    else:
        print(f"   No commits to push")

    # Stage the submodule update in parent repo
    _, stderr, returncode = run_command(["git", "add", submodule_path], check=False)
    if returncode != 0:
        print(f"   ✗ Failed to stage submodule in parent: {stderr}", file=sys.stderr)
        return False

    print(f"   ✓ Staged submodule update in parent repo")
    return True


def main():
    """Main function to process all submodules."""
    print("🔍 Checking submodules for changes...")

    # Get all submodules
    submodules = get_submodules()
    if not submodules:
        print("   No submodules found")
        return 0

    # Check which submodules have changes
    changed_submodules = []
    for submodule in submodules:
        if submodule_has_changes(submodule):
            changed_submodules.append(submodule)

    if not changed_submodules:
        print("   ✓ No submodule changes detected")
        return 0

    print(f"\n📝 Found changes in: {', '.join(changed_submodules)}")

    # Get commit message template
    parent_msg = get_parent_commit_message()
    if parent_msg:
        commit_message = parent_msg
        print(f"\n💬 Using commit message: \"{commit_message}\"")
    else:
        commit_message = "auto: submodule updates"
        print(f"\n💬 Using default message: \"{commit_message}\"")

    # Process each submodule
    all_success = True
    for submodule in changed_submodules:
        if not commit_and_push_submodule(submodule, commit_message):
            all_success = False

    if all_success:
        print("\n✅ All submodules processed successfully")
        return 0
    else:
        print("\n❌ Some submodules failed to process", file=sys.stderr)
        print("   You may need to commit them manually", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)