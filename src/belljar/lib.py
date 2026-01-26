import functools
import inspect
import os
import threading
from pathlib import Path
from typing import Any, Callable, Union, cast

import dill
import xxhash

CONTEXT_PROPERTY_NAME = "__context"
DEFAULT_CACHE_DIR = Path(".jar")


class CacheHit(Exception):
    pass


class Fingerprint:
    def __init__(self, fingerprint: xxhash.xxh64) -> None:
        self._fingerprint = fingerprint

    def get(self) -> xxhash.xxh64:
        return self._fingerprint

    def update(self, value: Any) -> None:
        self._fingerprint.update(dill.dumps(value))


class CacheDir:
    def __init__(self, dir: Path) -> None:
        os.makedirs(dir, exist_ok=True)
        self.dir = dir

    @classmethod
    def file_name(cls, fingerprint: Fingerprint) -> str:
        digest = fingerprint.get().hexdigest()
        return digest + ".dill"

    def file_path(self, fingerprint: Fingerprint) -> Path:
        file_name = self.file_name(fingerprint)
        return self.dir / file_name

    def file_exists(self, fingerprint: Fingerprint) -> bool:
        file_path = self.file_path(fingerprint)
        return os.path.exists(file_path)


class TaskCache:
    def __init__(
        self,
        cache_dir: CacheDir,
        fingerprint: Fingerprint,
    ) -> None:
        self._cache_dir = cache_dir
        self._fingerprint = fingerprint

    def update(self, value: Any) -> None:
        self._fingerprint.update(value)

    def exists(self) -> bool:
        return self._cache_dir.file_exists(self._fingerprint)

    def save(self, output: Any) -> None:
        file_path = self._cache_dir.file_path(self._fingerprint)
        with open(file_path, "wb") as f:
            dill.dump(output, f)

    def load(self) -> Any:
        file_path = self._cache_dir.file_path(self._fingerprint)
        with open(file_path, "rb") as f:
            return dill.load(f)


class Context:
    def __init__(self) -> None:
        self.tasks: list[TaskCache] = []

    def push(self, task_cache: TaskCache) -> None:
        self.tasks.append(task_cache)

    def task_cache(self) -> TaskCache:
        return self.tasks[-1]

    def pop(self) -> None:
        self.tasks.pop()


class ThreadContext(threading.local):
    def __init__(self) -> None:
        setattr(self, CONTEXT_PROPERTY_NAME, Context())


thread_context = ThreadContext()


def check():
    context = cast(Context, getattr(thread_context, CONTEXT_PROPERTY_NAME))
    task_cache = context.task_cache()
    if task_cache.exists():
        raise CacheHit()


def include(value: Any) -> None:
    context = cast(Context, getattr(thread_context, CONTEXT_PROPERTY_NAME))
    task_cache = context.task_cache()
    task_cache.update(value)


def store(dir: Union[Path, Callable] = DEFAULT_CACHE_DIR) -> Callable:
    def factory(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            context = cast(Context, getattr(thread_context, CONTEXT_PROPERTY_NAME))
            cache_dir = CacheDir(dir if not callable(dir) else DEFAULT_CACHE_DIR)
            fingerprint = Fingerprint(xxhash.xxh64())
            fingerprint.update(dill.source.getname(func))
            fingerprint.update(dill.source.getmodule(func))
            fingerprint.update(dill.source.getsource(func))
            task_cache = TaskCache(cache_dir, fingerprint)
            context.push(task_cache)

            try:
                output = func(*args, **kwargs)
                task_cache.save(output)
                return output
            except CacheHit:
                return task_cache.load()
            finally:
                context.pop()

        return wrapper

    if callable(dir):
        return factory(dir)

    return factory
