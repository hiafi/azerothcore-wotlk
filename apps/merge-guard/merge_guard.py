#!/usr/bin/env python3
"""
merge-guard: catch fork edits that an upstream merge silently dropped.

An edit to an upstream-owned file can vanish in a merge without any conflict - e.g. when upstream
moves the function it lived in to another file (docs/bugs-and-fixes.md, "A `// Custom:` core edit
silently disappears after an upstream merge"). Conflicts are loud; silent drops are the danger.

How it works (no manifest, no markers needed - everything comes from git history):
  1. Baseline = the fork before the merge (default: HEAD while a merge is in progress, HEAD^1 once
     the merge is committed, otherwise HEAD). Its upstream = merge-base(baseline, upstream ref).
  2. For every file the fork had modified relative to that upstream, the "fork lines" are the
     lines present in the baseline copy but not in the upstream copy (a per-file multiset, blank
     and punctuation-only lines ignored).
  3. Each fork line must still be in the same file in the working tree (the merge result). Any
     that aren't are reported MISSING, with the other files touched by the merge where the same
     line now appears ("moved?") - that's the upstream-moved-the-function case. A vanished line with
     a similar new fork line in the same file (conflict resolution / reformatting) is reported as
     CHANGED instead and doesn't fail the check.
Lines upstream itself dropped are not blamed on the merge.

Usage (from anywhere inside the repo):
  python3 apps/merge-guard/merge_guard.py check              # after (or during) an upstream merge
  python3 apps/merge-guard/merge_guard.py check --baseline <rev>
  python3 apps/merge-guard/merge_guard.py check --baseline <pre> --result <merge> --upstream <up>  # audit a past merge
  python3 apps/merge-guard/merge_guard.py list               # fork lines per modified upstream file
Options:
  --upstream REF   upstream ref (default: upstream/Playerbot; `git fetch upstream` first)

Exit code: 0 = no fork line missing, 1 = at least one missing, 2 = usage/setup error.
Limitation: a pure deletion of upstream lines (nothing added) is invisible - leave a
`// Custom:` comment at the spot so the edit has a line to track.
"""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
from collections import Counter
from pathlib import Path

DEFAULT_UPSTREAM = "upstream/Playerbot"
SIGNIFICANT_RE = re.compile(r"[A-Za-z0-9]")
MIN_LINE_LENGTH = 6
MAX_SHOWN_LINE = 150
IDENT_RE = re.compile(r"[A-Za-z_]\w{2,}")
SIMILARITY = 0.6  # identifier-set Jaccard above which a vanished line counts as reworded, not lost


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, errors="replace")
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def rev_exists(repo: Path, rev: str) -> bool:
    return bool(git(repo, "rev-parse", "--verify", "-q", f"{rev}^{{commit}}", check=False).strip())


def normalize(line: str) -> str | None:
    text = " ".join(line.split())
    if len(text) < MIN_LINE_LENGTH or not SIGNIFICANT_RE.search(text):
        return None
    return text


def line_counts(text: str | None) -> Counter:
    counts: Counter = Counter()
    if text is None:
        return counts
    for line in text.splitlines():
        key = normalize(line)
        if key:
            counts[key] += 1
    return counts


def show(repo: Path, rev: str, path: str) -> str | None:
    """File content at rev, or None if it doesn't exist there."""
    result = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=repo, capture_output=True, text=True,
                            errors="replace")
    return result.stdout if result.returncode == 0 else None


def worktree(repo: Path, path: str) -> str | None:
    file_path = repo / path
    return file_path.read_text(encoding="utf-8", errors="replace") if file_path.is_file() else None


def modified_text_files(repo: Path, old: str, new: str | None) -> list[str]:
    """Files present in both revs (new=None: working tree) whose content differs; binaries skipped."""
    args = ["diff", "--numstat", "--diff-filter=M", old] + ([new] if new else [])
    files = []
    for row in git(repo, *args).splitlines():
        added, removed, path = row.split("\t", 2)
        if added != "-" and removed != "-":
            files.append(path)
    return files


def fork_lines(base_upstream: Counter, fork: Counter) -> Counter:
    return Counter({line: count - base_upstream.get(line, 0) for line, count in fork.items()
                    if count > base_upstream.get(line, 0)})


def best_match(line: str, candidates: Counter) -> str | None:
    """The candidate sharing most identifiers with `line`, if similar enough to call it a rewording."""
    idents = set(IDENT_RE.findall(line))
    if len(idents) < 2:
        return None
    best, best_score = None, 0.0
    for candidate in candidates:
        other = set(IDENT_RE.findall(candidate))
        score = len(idents & other) / len(idents | other) if other else 0.0
        if score > best_score:
            best, best_score = candidate, score
    return best if best_score >= SIMILARITY else None


def clip(line: str) -> str:
    return line if len(line) <= MAX_SHOWN_LINE else line[:MAX_SHOWN_LINE] + "..."


def pick_baseline(repo: Path) -> tuple[str, str]:
    git_dir = Path(git(repo, "rev-parse", "--git-dir").strip())
    if not git_dir.is_absolute():
        git_dir = repo / git_dir
    if (git_dir / "MERGE_HEAD").exists():
        return "HEAD", "merge in progress: comparing the working tree with HEAD"
    parents = git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()
    if len(parents) > 2:
        return "HEAD^1", "HEAD is a merge commit: comparing the working tree with its first parent"
    return "HEAD", "no merge detected: comparing the working tree with HEAD"


def cmd_list(repo: Path, upstream: str) -> int:
    base_upstream = git(repo, "merge-base", "HEAD", upstream).strip()
    total = 0
    for path in modified_text_files(repo, base_upstream, None):
        lines = fork_lines(line_counts(show(repo, base_upstream, path)), line_counts(worktree(repo, path)))
        if lines:
            count = sum(lines.values())
            total += count
            print(f"{count:5d}  {path}")
    print(f"\n{total} fork line(s) in upstream-owned files (working tree vs {upstream} @ {base_upstream[:12]})")
    return 0


def cmd_check(repo: Path, upstream: str, baseline: str | None, result: str | None) -> int:
    note = ""
    if result is not None and baseline is None:
        baseline = f"{result}^1"
    if baseline is None:
        baseline, note = pick_baseline(repo)
    for label, rev in (("Baseline", baseline), ("Result", result)):
        if rev is not None and not rev_exists(repo, rev):
            print(f"{label} '{rev}' not found.", file=sys.stderr)
            return 2

    def current_content(path: str) -> str | None:
        return show(repo, result, path) if result else worktree(repo, path)

    base_upstream = git(repo, "merge-base", baseline, upstream).strip()
    print(f"baseline {baseline} ({git(repo, 'rev-parse', '--short', baseline).strip()}), its upstream "
          f"{base_upstream[:12]}, new upstream {upstream} ({git(repo, 'rev-parse', '--short', upstream).strip()})")
    print(f"result: {result or 'working tree'}")
    if note:
        print(note)

    diff_args = ["diff", "--name-only", baseline] + ([result] if result else [])
    touched = set(git(repo, *diff_args).splitlines())  # files the merge changed
    touched_counts: dict[str, Counter] = {}

    def counts_for_touched(path: str) -> Counter:
        if path not in touched_counts:
            touched_counts[path] = line_counts(current_content(path))
        return touched_counts[path]

    missing_total = 0
    changed_total = 0
    files_checked = 0
    lines_checked = 0
    for path in modified_text_files(repo, base_upstream, baseline):
        base_up = line_counts(show(repo, base_upstream, path))
        base_fork = line_counts(show(repo, baseline, path))
        ours = fork_lines(base_up, base_fork)
        if not ours:
            continue
        files_checked += 1
        lines_checked += sum(ours.values())
        if path not in touched:
            continue  # the merge didn't change this file, so nothing can have been dropped
        current = line_counts(current_content(path))
        new_up = line_counts(show(repo, upstream, path))
        # fork lines in the merge result that weren't fork lines before: candidates for a rewording
        reworded_candidates = fork_lines(new_up, current) - ours
        for line, count in sorted(ours.items()):
            dropped = base_fork[line] - current.get(line, 0)
            if dropped <= 0:
                continue
            upstream_dropped = max(0, base_up.get(line, 0) - new_up.get(line, 0))
            lost = min(count, dropped - upstream_dropped)
            if lost <= 0:
                continue
            match = best_match(line, reworded_candidates)
            if match:
                changed_total += lost
                print(f"CHANGED  {path}  x{lost}\n           was: {clip(line)}\n           now: {clip(match)}")
                continue
            missing_total += lost
            moved = sorted(p for p in touched if p != path and counts_for_touched(p).get(line))
            hint = f"\n           moved? now in: {', '.join(moved)}" if moved else ""
            print(f"MISSING  {path}  x{lost}\n           {clip(line)}{hint}")

    print(f"\nchecked {lines_checked} fork line(s) in {files_checked} upstream-owned file(s)")
    if changed_total:
        print(f"{changed_total} fork line(s) CHANGED: reworded during the merge (a similar fork line is in the "
              "same file). Eyeball them; they don't fail the check.")
    if missing_total:
        print(f"{missing_total} fork line(s) MISSING. The merge dropped fork edits, or upstream moved the code "
              "they lived in (see the 'moved?' hints and `git log -p <upstream> -- <file>`). Re-apply them "
              "before committing the merge.")
        return 1
    print("OK: every fork line is still in place.")
    return 0


def main() -> int:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # allow `| head` without a traceback
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="check", choices=("check", "list"))
    parser.add_argument("--upstream", default=DEFAULT_UPSTREAM)
    parser.add_argument("--baseline", help="pre-merge revision (default: auto-detected, see above)")
    parser.add_argument("--result", help="merge result revision to check instead of the working tree "
                        "(default baseline then becomes RESULT^1)")
    args = parser.parse_args()

    repo = Path(git(Path(__file__).resolve().parent, "rev-parse", "--show-toplevel").strip())
    if not rev_exists(repo, args.upstream):
        print(f"Upstream ref '{args.upstream}' not found. Run `git fetch upstream` first "
              "(or pass --upstream REF).", file=sys.stderr)
        return 2
    if args.command == "list":
        return cmd_list(repo, args.upstream)
    return cmd_check(repo, args.upstream, args.baseline, args.result)


if __name__ == "__main__":
    sys.exit(main())
