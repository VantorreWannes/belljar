import functools
import inspect
import os
import threading
from pathlib import Path
from typing import Any, Callable, Union, cast

import dill
import xxhash

_context = threading.local()
_CACHE_PROPERTY_NAME = "cache"
CACHE_DIR = Path(".jar")


class _CacheHit(Exception):
    def __init__(self, fingerprint: xxhash.xxh64) -> None:
        self.fingerprint = fingerprint


class _CacheState:
    def __init__(self, dir: Path) -> None:
        os.makedirs(dir, exist_ok=True)
        self.dir: Path = dir
        self._fingerprint = xxhash.xxh64()

    def fingerprint(self) -> xxhash.xxh64:
        return self._fingerprint

    def update(self, value: Any) -> None:
        self._fingerprint.update(dill.dumps(value))

    def path(self) -> Path:
        digest = self._fingerprint.hexdigest()
        filename = digest + ".dill"
        return self.dir / filename

    def exists(self) -> bool:
        return os.path.exists(self.path())


def includes(value: Any) -> None:
    if hasattr(_context, _CACHE_PROPERTY_NAME):
        cache = cast(_CacheState, getattr(_context, _CACHE_PROPERTY_NAME))
        cache.update(value)
        if cache.exists():
            raise _CacheHit(cache.fingerprint())


def jar(dir: Union[Path, Callable] = CACHE_DIR) -> Callable:
    def factory(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            state = _CacheState(dir if not callable(dir) else CACHE_DIR)
            state.update(func.__module__)
            state.update(func.__name__)
            state.update(inspect.getsource(func))
            state.update(args)
            state.update(kwargs)

            setattr(_context, _CACHE_PROPERTY_NAME, state)

            try:
                if state.exists():
                    with open(state.path(), "rb") as f:
                        return dill.load(f)

                output = func(*args, **kwargs)

                with open(state.path(), "wb") as f:
                    dill.dump(output, f)
                    return output

            except _CacheHit:
                with open(state.path(), "rb") as f:
                    return dill.load(f)
            finally:
                delattr(_context, _CACHE_PROPERTY_NAME)

        return wrapper

    if callable(dir):
        return factory(dir)

    return factory


__all__ = ["jar", "includes"]
