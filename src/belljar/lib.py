import functools
import hashlib
import threading
from pathlib import Path
from typing import Any, Callable, Optional, Union

import dill


class Identity:
    def __init__(self, seed: Optional[bytes] = None):
        self._hash = hashlib.sha256(seed or b"")

    def update(self, value: Any):
        self._hash.update(dill.dumps(value))

    @property
    def key(self) -> str:
        return self._hash.hexdigest()


class Registry(threading.local):
    def __init__(self):
        self.stack: list[tuple[Identity, Path]] = []

    def current(self) -> tuple[Identity, Path]:
        if not self.stack:
            raise RuntimeError("Out of belljar context.")
        return self.stack[-1]


_registry = Registry()


class Jar:
    @staticmethod
    def path_for(identity: Identity, root: Path) -> Path:
        return root / f"{identity.key}.dill"

    @staticmethod
    def load(identity: Identity, root: Path) -> Any:
        with open(Jar.path_for(identity, root), "rb") as f:
            return dill.load(f)

    @staticmethod
    def save(identity: Identity, root: Path, data: Any):
        path = Jar.path_for(identity, root)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            dill.dump(data, f)


class CacheHit(Exception):
    pass


def include(value: Any):
    identity, _ = _registry.current()
    identity.update(value)


def check():
    identity, root = _registry.current()
    if Jar.path_for(identity, root).exists():
        raise CacheHit()


def store(path_or_func: Union[Path, Callable] = Path(".jar")):
    root_path = path_or_func if isinstance(path_or_func, Path) else Path(".jar")

    def decorator(func: Callable):
        static_seed = dill.dumps((func.__name__, dill.source.getsource(func)))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            identity = Identity(static_seed)

            _registry.stack.append((identity, root_path))
            try:
                result = func(*args, **kwargs)
                Jar.save(identity, root_path, result)
                return result
            except CacheHit:
                return Jar.load(identity, root_path)
            finally:
                _registry.stack.pop()

        return wrapper

    return decorator(path_or_func) if callable(path_or_func) else decorator
