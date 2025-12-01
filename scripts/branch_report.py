"""
Branch delta report for cloned repositories in ./repos.

Shows how many commits each remote branch is ahead of its remote main branch
to help decide which timelines need review before consolidation.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict


def run_git(repo: Path, args: list[str], check: bool = True) -> str:
    """Run git command in repo and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def main() -> None:
    repos_root = Path("repos")
    if not repos_root.exists():
        raise SystemExit("repos directory not found")

    for repo in sorted(repos_root.iterdir()):
        if not (repo / ".git").exists():
            continue

        print(f"\n=== {repo.name} ===")
        subprocess.run(
            ["git", "-C", str(repo), "fetch", "--all", "--prune"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            branch_output = run_git(repo, ["branch", "-r"])
        except subprocess.CalledProcessError:
            print("  (no remote branches)")
            continue

        branches = [
            line.strip()
            for line in branch_output.splitlines()
            if line.strip() and "->" not in line
        ]
        if not branches:
            print("  (no remote branches)")
            continue

        baselines: Dict[str, str] = {}
        for br in branches:
            remote = br.split("/", 1)[0]
            candidate = f"{remote}/main"
            if remote in baselines:
                continue
            try:
                run_git(repo, ["rev-parse", "--verify", candidate])
                baselines[remote] = candidate
            except subprocess.CalledProcessError:
                continue

        for br in branches:
            remote = br.split("/", 1)[0]
            baseline = baselines.get(remote)
            if not baseline or br == baseline:
                continue
            try:
                ahead = run_git(
                    repo,
                    ["rev-list", "--count", f"{baseline}..{br}"],
                )
            except subprocess.CalledProcessError:
                print(f"  {br}: unable to compare")
                continue
            status = "merged" if ahead == "0" else f"+{ahead} commits"
            print(f"  {br}: {status}")


if __name__ == "__main__":
    main()


