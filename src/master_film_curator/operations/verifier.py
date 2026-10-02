import hashlib
from pathlib import Path


class SafetyError(RuntimeError):
    pass


def digest(path: Path, mode="sha256") -> str | None:
    if mode == "size":
        return None
    h = hashlib.sha256()
    with path.open("rb") as stream:
        if mode == "quick_hash":
            size = path.stat().st_size
            h.update(str(size).encode())
            for offset in sorted({0, max(0, size // 2 - 524288), max(0, size - 1048576)}):
                stream.seek(offset)
                h.update(stream.read(1048576))
        elif mode == "sha256":
            for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                h.update(block)
        else:
            raise ValueError("Unknown verification mode")
    return h.hexdigest()


def no_symlinks(path: Path):
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise SafetyError(f"Symlink path refused: {part}")


def snapshot(path: Path, mode="sha256") -> dict:
    no_symlinks(path)
    before = path.stat()
    if not path.is_file():
        raise SafetyError(f"Not a regular file: {path}")
    hashed = digest(path, mode)
    after = path.stat()
    keys = ("st_size", "st_mtime_ns", "st_ino", "st_dev")
    if any(getattr(before, k) != getattr(after, k) for k in keys):
        raise SafetyError(f"File changed during verification: {path}")
    return {
        "size": after.st_size,
        "mtime_ns": after.st_mtime_ns,
        "inode": after.st_ino,
        "device": after.st_dev,
        "mode": mode,
        "digest": hashed,
    }


def check_snapshot(path: Path, expected: dict, identity=True):
    actual = snapshot(path, expected["mode"])
    fields = ["size", "digest"] + (["mtime_ns", "inode", "device"] if identity else [])
    if any(actual[k] != expected[k] for k in fields):
        raise SafetyError(f"File changed or verification failed: {path}")
    return actual


def case_collision(path: Path) -> Path | None:
    # Check every existing component for Windows-equivalent aliases, including on ext4.
    current = Path(path.anchor)
    parts = path.parts[1:]
    for i, part in enumerate(parts):
        if not current.is_dir():
            return current if current.exists() else None
        matches = [
            p for p in current.iterdir() if p.name.rstrip(" .").casefold() == part.rstrip(" .").casefold()
        ]
        if not matches:
            return None
        chosen = next((p for p in matches if p.name == part), matches[0])
        if chosen.name != part or len(matches) > 1 or i == len(parts) - 1:
            return chosen
        current = chosen
    return None
