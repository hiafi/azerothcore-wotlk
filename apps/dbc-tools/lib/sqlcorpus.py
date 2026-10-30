"""
Shared access to the SQL corpus (base dumps, `db_world`, `pending_db_world`, module SQL) for one `generate.py` run.

Every loader in this tool (`state`, `trainer_state`, `spell_tables`) replays the same ~1,300 files, each for its own
table. Left alone that means reading every file dozens of times, scanning each file's statement heads once per table,
and re-parsing identical base dumps. This module is the one place that owns the files for a run:

- `read_text(path)`: the file's text, read once and shared (a `SqlText`, which is a `str`).
- `SqlText.head_index`: where every statement head (`INSERT INTO`/`DELETE FROM`/`UPDATE .. SET`/`SET @v :=`) sits,
  scanned once per file and shared by every table's replay (`sql_dump._next_statement` and friends use it instead of
  re-running the head regex over the whole text per table).
- `mentions(path, table)`: whether a file names a table (`` `table` `` anywhere in it), shared and persisted.
- `checkpointed(...)`: the disk cache. A loader's replay of the base dump plus the (immutable) promoted `db_world`
  files is stored as a pickled snapshot; the next run reloads it instead of replaying, and extends it when files were
  appended. See that method for the invalidation rules.

**Off by default.** Without `activate()` nothing is memoised and nothing touches the disk: `read_text` is a plain
`Path.read_text`, `mentions` a plain substring test, `checkpointed` just runs the replay. So tests and the other tools
keep their old behaviour, and a loader has exactly one implementation (the cache is a wrapper around it, never a
second code path). `generate.py` activates it; it never changes what a loader returns or prints.

**Staleness.** Memoised texts assume the files do not change while the run is active. `generate.py` reads every SQL
file before it writes its own pending SQL (the last step that touches that directory) and calls `deactivate()` when
the run ends.
"""

from __future__ import annotations

import bisect
import contextlib
import hashlib
import io
import json
import os
import pickle
import re
import shutil
import sys
from pathlib import Path
from typing import Callable

# `INSERT`/`REPLACE`, `DELETE`, `UPDATE .. SET` and an integer `SET @var := n;` in one alternation, a distinctly
# named table group per branch (Python's `re` forbids reusing a group name across alternatives). Lives here (not in
# `sql_dump`, which imports it) so the head index and the per-table replays can never disagree about what a head is.
STATEMENT_HEAD_RE = re.compile(
    r"(?:INSERT|REPLACE)\s+INTO\s+`(?P<ins_table>\w+)`\s*(?:\((?P<cols>[^)]*)\))?\s*VALUES\s*"
    r"|DELETE\s+FROM\s+`(?P<del_table>\w+)`\s*"
    r"|UPDATE\s+`(?P<upd_table>\w+)`\s+SET\s+"
    r"|SET\s+(?P<set_name>@\w+)\s*:?=\s*(?P<set_value>-?\d+)\s*;",
    re.IGNORECASE,
)

FORMAT_VERSION = 1
_MAGIC = b"DBCTOOLS-CACHE\n"


class HeadMatch:
    """The `re.Match` surface the replay loops use (`group`, `start`, `end`) over one entry of a `HeadIndex`.

    An entry is `(start, end, kind, table, cols, set_value)`; `kind` is `I` (insert/replace), `D`, `U` or `S` (a
    `SET @var := n;`, whose `table` slot holds the variable name)."""

    __slots__ = ("_head",)

    def __init__(self, head: tuple):
        self._head = head

    def start(self) -> int:
        return self._head[0]

    def end(self) -> int:
        return self._head[1]

    def group(self, name: str):
        _start, _end, kind, table, cols, set_value = self._head
        if name == "cols":
            return cols if kind == "I" else None
        if name == "table":  # the two single-purpose patterns (`_INSERT_HEAD_RE`, `_DELETE_HEAD_RE`)
            return table if kind in ("I", "D") else None
        if name == "ins_table":
            return table if kind == "I" else None
        if name == "del_table":
            return table if kind == "D" else None
        if name == "upd_table":
            return table if kind == "U" else None
        if name == "set_name":
            return table if kind == "S" else None
        if name == "set_value":
            return set_value if kind == "S" else None
        raise IndexError(f"no such group {name!r}")


_CANDIDATE_RE = re.compile(r"insert|replace|delete|update|set")


def _head_entry(m: re.Match) -> tuple:
    if m.group("ins_table") is not None:
        return (m.start(), m.end(), "I", m.group("ins_table"), m.group("cols"), None)
    if m.group("del_table") is not None:
        return (m.start(), m.end(), "D", m.group("del_table"), None, None)
    if m.group("upd_table") is not None:
        return (m.start(), m.end(), "U", m.group("upd_table"), None, None)
    return (m.start(), m.end(), "S", m.group("set_name"), None, m.group("set_value"))


def scan_heads(text: str) -> list[tuple]:
    """Every statement head in `text`, in order (the same non-overlapping left-to-right scan `re.search` in a loop
    would do from position 0).

    Running the case-insensitive alternation at every character is slow (about 7 MB/s). Every head starts with one of
    five keywords, so a plain lowercase search for those finds the only places a head can start, and the full pattern
    is tried just there (6x faster, same result for any head spelled in ASCII). It needs `lower()` to keep every offset,
    which it does unless the text holds a character whose lowercase is longer; such a file takes the plain scan. (A
    keyword spelled with a letter that only case-folds to ASCII, such as a dotless i or a long s, would be missed.)"""
    low = text.lower()
    if len(low) != len(text):
        return [_head_entry(m) for m in STATEMENT_HEAD_RE.finditer(text)]
    heads = []
    pos = 0
    try_match = STATEMENT_HEAD_RE.match
    for candidate in _CANDIDATE_RE.finditer(low):
        start = candidate.start()
        if start < pos:
            continue
        m = try_match(text, start)
        if m is not None:
            heads.append(_head_entry(m))
            pos = m.end()
    return heads


class HeadIndex:
    """Statement heads of one file, queryable per table.

    `first(pos, table, kinds)` is the first head starting at or after `pos` that is one of `kinds` and (for I/D/U)
    names `table`; a `SET @var` head is never table-filtered, exactly like `sql_dump._next_statement`'s regex loop."""

    def __init__(self, heads: list[tuple]):
        self.heads = heads
        self._starts = [h[0] for h in heads]
        self._filtered: dict[tuple, tuple[list[int], list[tuple]]] = {}

    def overlaps(self, pos: int) -> bool:
        """Whether a head found by the one-pass scan starts before `pos` and runs past it. That only happens when the
        scan matched head-looking text inside a string or comment of a statement the replay then skipped; a regex
        search from `pos` would not have been blocked by it, so the caller must search the text instead."""
        j = bisect.bisect_left(self._starts, pos) - 1
        return j >= 0 and self.heads[j][1] > pos

    def first(self, pos: int, table: str, kinds: str) -> HeadMatch | None:
        key = (table, kinds)
        filtered = self._filtered.get(key)
        if filtered is None:
            chosen = [h for h in self.heads if h[2] in kinds and (h[2] == "S" or h[3] == table)]
            filtered = ([h[0] for h in chosen], chosen)
            self._filtered[key] = filtered
        starts, chosen = filtered
        i = bisect.bisect_left(starts, pos)
        return HeadMatch(chosen[i]) if i < len(chosen) else None


class SqlText(str):
    """A file's text plus what the corpus knows about it. Behaves as the plain `str` the replays always took."""

    corpus: "Corpus"
    path: Path
    digest: str

    @property
    def head_index(self) -> HeadIndex:
        index = self.__dict__.get("_head_index")
        if index is None:
            index = HeadIndex(self.corpus._heads_for(self))
            self.__dict__["_head_index"] = index
        return index


def _universal_newlines(text: str) -> str:
    """What `Path.read_text` does on decode: `\\r\\n` and a lone `\\r` both become `\\n`."""
    if "\r" in text:
        return text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CacheError(Exception):
    """A cache file that cannot be trusted (truncated, wrong version, wrong checksum, wrong key)."""


def _pack(obj: object, header: dict) -> bytes:
    payload = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    header = {**header, "format": FORMAT_VERSION, "length": len(payload), "sha": _digest(payload)}
    return _MAGIC + json.dumps(header, sort_keys=True).encode() + b"\n" + payload


def _unpack(blob: bytes, expect: dict) -> object:
    if not blob.startswith(_MAGIC):
        raise CacheError("bad magic")
    rest = blob[len(_MAGIC):]
    newline = rest.find(b"\n")
    if newline < 0:
        raise CacheError("no header")
    header = json.loads(rest[:newline])
    payload = rest[newline + 1:]
    if header.get("format") != FORMAT_VERSION:
        raise CacheError("format version")
    for key, value in expect.items():
        if header.get(key) != value:
            raise CacheError(f"header mismatch on {key}")
    if header.get("length") != len(payload) or header.get("sha") != _digest(payload):
        raise CacheError("payload checksum")
    return pickle.loads(payload)


def _write_atomic(path: Path, blob: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp{os.getpid()}")
    try:
        tmp.write_bytes(blob)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def code_version(roots: list[Path], extra: str = "") -> str:
    """Hash of every non-test `*.py` under `roots`, `extra` and the Python version (pickle layouts and `re`
    behaviour). `generate.cache_code_version` passes the item overlay's package here and adds the loader modules
    itself; a change to any of them makes every snapshot a miss."""
    h = hashlib.sha256()
    h.update(sys.version.encode())
    h.update(extra.encode())
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            if path.name.startswith("test_") or "__pycache__" in path.parts:
                continue
            h.update(str(path.relative_to(root)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()[:24]


class Corpus:
    """One run's view of the SQL files, plus the on-disk cache. Use `activate()`; do not build directly."""

    def __init__(self, cache_dir: Path | None, version: str, rebuild: bool = False):
        self.cache_dir = cache_dir
        self.version = version
        self.rebuild = rebuild  # ignore what is on disk, still write
        self._texts: dict[str, SqlText] = {}
        self._digests: dict[str, str] = {}
        self._mentions: dict[tuple, bool] = {}
        self._index: dict[str, dict] | None = None  # file digest -> {"heads": [...], "m": {key: bool}}
        self._index_dirty = False
        self._seen_digests: set[str] = set()
        self.stats = {"hit": 0, "extend": 0, "miss": 0, "corrupt": 0}

    # -- files ---------------------------------------------------------------------------------------------------

    def _read_bytes(self, path: Path) -> bytes:
        return Path(path).read_bytes()

    def digest(self, path: Path) -> str:
        key = str(path)
        found = self._digests.get(key)
        if found is None:
            text = self._texts.get(key)
            found = text.digest if text is not None else _digest(self._read_bytes(path))
            self._digests[key] = found
        return found

    def read_text(self, path: Path) -> SqlText:
        key = str(path)
        text = self._texts.get(key)
        if text is None:
            data = self._read_bytes(path)
            text = SqlText(_universal_newlines(data.decode("utf-8")))
            text.corpus, text.path, text.digest = self, Path(path), _digest(data)
            self._texts[key] = text
            self._digests[key] = text.digest
        return text

    # -- persisted per-file index ---------------------------------------------------------------------------------

    def _index_path(self) -> Path | None:
        return self.cache_dir / "fileindex.bin" if self.cache_dir else None

    def _load_index(self) -> dict[str, dict]:
        if self._index is None:
            self._index = {}
            path = self._index_path()
            if path is not None and path.is_file() and not self.rebuild:
                try:
                    self._index = _unpack(path.read_bytes(), {"kind": "fileindex", "code": self.version})
                except Exception:
                    self.stats["corrupt"] += 1
                    self._index = {}
        return self._index

    def _entry(self, digest: str) -> dict:
        index = self._load_index()
        entry = index.get(digest)
        if entry is None:
            entry = index[digest] = {}
            self._index_dirty = True
        self._seen_digests.add(digest)
        return entry

    def _heads_for(self, text: SqlText) -> list[tuple]:
        entry = self._entry(text.digest)
        heads = entry.get("heads")
        if heads is None:
            heads = entry["heads"] = scan_heads(text)
            self._index_dirty = True
        return heads

    def mentions(self, path: Path, table: str, loose: bool = False) -> bool:
        """Whether the file names `table` in backticks (or, `loose`, also bare as a word)."""
        key = (str(path), table, loose)
        found = self._mentions.get(key)
        if found is None:
            digest = self.digest(path)
            entry = self._entry(digest)
            persisted = entry.setdefault("m", {})
            found = persisted.get((table, loose))
            if found is None:
                text = self.read_text(path)
                found = f"`{table}`" in text or (
                    loose and re.search(rf"\b{re.escape(table)}\b", text, re.IGNORECASE) is not None
                )
                persisted[(table, loose)] = found
                self._index_dirty = True
            self._mentions[key] = found
        return found

    # -- snapshots ------------------------------------------------------------------------------------------------

    def _snapshot_path(self, key: str) -> Path | None:
        return self.cache_dir / f"snap-{key}.bin" if self.cache_dir else None

    def checkpointed(
        self, kind: str, params: object, stable: list[Path], init: Callable[[], object],
        step: Callable[[object, Path], object],
    ) -> tuple[object, str]:
        """`state = init(); for path in stable: state = step(state, path)`, remembered on disk.

        Returns `(state, printed)`: `printed` is what the replay wrote to stdout (the loaders warn about statements
        they cannot apply), captured so a cache hit can print the identical text; the caller writes it to stdout
        right away, as the uncached replay would have printed it live. What it wrote to stderr is captured the same
        way and written to stderr here.

        The snapshot is keyed by `(kind, params, code version)` and stores the ordered `(path, content hash)` list it
        was built from. It is used when that list is a prefix of the current `stable` list (the files appended since,
        the usual case after a promotion, are replayed on top and the snapshot is rewritten); any other difference (a
        file edited, removed, or inserted before the end) rebuilds from scratch. A corrupt, truncated or stale file is
        a miss, never an error: the answer then comes from the full replay. `step` must be a pure function of the
        file contents and the code; whatever the caller replays after this (pending and module files, which change
        every run) is applied to the returned object and is not part of the snapshot."""
        files = [(str(p), self.digest(p)) for p in stable]
        name = hashlib.sha256(repr((kind, params, self.version)).encode()).hexdigest()[:20]
        path = self._snapshot_path(f"{kind}-{name}")
        header = {"kind": kind, "code": self.version, "params": repr(params)}
        cached = None
        if path is not None and path.is_file() and not self.rebuild:
            try:
                cached = _unpack(path.read_bytes(), header)
            except Exception:
                self.stats["corrupt"] += 1
                cached = None
        done = 0
        if cached is not None:
            done = len(cached["files"])
            if done > len(files) or cached["files"] != files[:done]:
                cached, done = None, 0
        if cached is not None and done == len(files):
            self.stats["hit"] += 1
            sys.stderr.write(cached.get("err", ""))
            return cached["state"], cached["out"]
        # Label each file the replay is about to read with the hash of the very text it will read (the memoised copy
        # `step` gets), not of an earlier read of the same path: a file rewritten in between must not be stored under
        # the old hash. (A binary input, the extracted .dbc, is hashed once and read once by its own reader.)
        for i in range(done, len(stable)):
            if stable[i].suffix == ".sql":
                files[i] = (str(stable[i]), self.read_text(stable[i]).digest)
        buf, err_buf = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err_buf):
                if cached is None:
                    state = init()
                    out_before = err_before = ""
                else:
                    state, out_before, err_before = cached["state"], cached["out"], cached.get("err", "")
                for p in stable[done:]:
                    state = step(state, p)
        except BaseException:
            sys.stdout.write((cached["out"] if cached is not None else "") + buf.getvalue())
            sys.stderr.write((cached.get("err", "") if cached is not None else "") + err_buf.getvalue())
            raise
        self.stats["extend" if cached is not None else "miss"] += 1
        out = out_before + buf.getvalue()
        err = err_before + err_buf.getvalue()
        sys.stderr.write(err)
        if path is not None:
            try:
                _write_atomic(path, _pack({"files": files, "state": state, "out": out, "err": err}, header))
            except OSError as exc:  # a read-only or full cache dir must not fail the run
                print(f"warning: dbc-tools cache: could not write {path.name}: {exc}", file=sys.stderr)
        # The caller mutates `state` (it replays pending files on top); the blob on disk stays as written above.
        return state, out

    # -- lifecycle ------------------------------------------------------------------------------------------------

    def close(self) -> None:
        """Persist the per-file index (entries for files seen this run only, so edited and deleted files age out)."""
        path = self._index_path()
        if path is None or self._index is None:
            return
        keep = self._seen_digests | set(self._digests.values())
        pruned = {digest: entry for digest, entry in self._index.items() if digest in keep}
        if not self._index_dirty and len(pruned) == len(self._index):
            return
        try:
            _write_atomic(path, _pack(pruned, {"kind": "fileindex", "code": self.version}))
        except OSError as exc:
            print(f"warning: dbc-tools cache: could not write {path.name}: {exc}", file=sys.stderr)


_ACTIVE: Corpus | None = None
_RESETS: list[Callable[[], None]] = []


def register_reset(fn: Callable[[], None]) -> None:
    """Run `fn` whenever a corpus is activated or deactivated (modules keep their per-run memos in dicts)."""
    _RESETS.append(fn)


def active() -> Corpus | None:
    return _ACTIVE


def activate(cache_dir: Path | None, version: str, rebuild: bool = False) -> Corpus:
    """Start memoising (and, with a `cache_dir`, caching) for this process. Returns the corpus."""
    global _ACTIVE
    for fn in _RESETS:
        fn()
    if cache_dir is not None:
        _prune_other_versions(cache_dir, version)
        cache_dir = cache_dir / version
    _ACTIVE = Corpus(cache_dir, version, rebuild)
    return _ACTIVE


def _prune_other_versions(base: Path, version: str, keep_others: int = 1) -> None:
    """Each code version caches in its own directory under `base`. Drop all but the `keep_others` most recently used
    of the other versions (a second checkout or branch on other code still gets one warm directory; the rest would
    only be dead weight, ~180 MB each)."""
    try:
        others = sorted(
            (p for p in base.iterdir() if p.is_dir() and p.name != version),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        for stale in others[keep_others:]:
            shutil.rmtree(stale, ignore_errors=True)
    except OSError:
        pass


def deactivate() -> None:
    """Stop memoising and persist the index. Call before writing files the loaders read."""
    global _ACTIVE
    corpus, _ACTIVE = _ACTIVE, None
    for fn in _RESETS:
        fn()
    if corpus is not None:
        corpus.close()


def read_text(path: Path) -> str:
    corpus = _ACTIVE
    if corpus is None:
        return Path(path).read_text(encoding="utf-8")
    return corpus.read_text(path)


def mentions(path: Path, table: str, loose: bool = False) -> bool:
    corpus = _ACTIVE
    if corpus is None:
        text = Path(path).read_text(encoding="utf-8")
        return f"`{table}`" in text or (
            loose and re.search(rf"\b{re.escape(table)}\b", text, re.IGNORECASE) is not None
        )
    return corpus.mentions(path, table, loose)


def checkpointed(
    kind: str, params: object, stable: list[Path], init: Callable[[], object], step: Callable[[object, Path], object],
) -> object:
    """`Corpus.checkpointed` when active (printing the captured output); a plain replay otherwise. Returns the state."""
    corpus = _ACTIVE
    if corpus is None:
        state = init()
        for path in stable:
            state = step(state, path)
        return state
    state, out = corpus.checkpointed(kind, params, stable, init, step)
    sys.stdout.write(out)
    return state
