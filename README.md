# belljar 🫙

**Mid-execution memoization for dynamic state.**

Standard caching fails when your function relies on hidden or changing state (like a database cursor or an open file). `belljar` solves this by letting you build the cache key _while_ the function runs.

```bash
uv add belljar
```

## The Difference

| Concept                    | `functools.lru_cache`            | `belljar`                                     |
| :------------------------- | :------------------------------- | :-------------------------------------------- |
| **When is it checked?**    | _Before_ the function runs.      | _Mid-execution_, exactly when you tell it to. |
| **What defines identity?** | Static function arguments.       | Function source code + runtime state.         |
| **Handling Mutable State** | Fails. Returns stale/wrong data. | Succeeds. Hashes current state dynamically.   |

## Usage

You need exactly three primitives: `@store` to set the boundary, `include()` to build identity, and `check()` to short-circuit.

```python
import belljar
import io

# A simulated file. The object stays the same, but its internal cursor moves.
log_file = io.StringIO("chunk1 chunk2 chunk3")

@belljar.store  # Automatically seeds identity using this function's source code
def process_chunk(file_handle):
    # 1. Add the file's exact runtime cursor position to the identity hash
    belljar.include(file_handle.tell())

    # 2. If we've processed from this exact position before, STOP.
    # The function aborts right here and returns the saved result from disk.
    belljar.check()

    # 3. Otherwise, do the heavy processing
    print("Doing heavy work...")
    return file_handle.read(6)

# Call 1: Reads "chunk1", saves to disk. (Takes time)
process_chunk(log_file)

# Call 2: Reads "chunk2", saves to disk. (Takes time)
process_chunk(log_file)

# If we reset the file and run it again:
log_file.seek(0)

# Call 3: belljar.check() detects the cursor is at 0, aborts the function,
# and instantly returns the cached "chunk1".
process_chunk(log_file)
```

## Core Mechanics

- **Auto-Invalidation:** `belljar` hashes your actual source code. If you edit the function, the cache invalidates automatically.
- **Disk Persistent:** Caches are saved to a `.jar/` directory by default, surviving script restarts. Pass a path to change it: `@store(Path("/tmp/cache"))`.
- **Deep Serialization:** Powered by `dill` (not `pickle`), meaning it safely handles lambdas, nested classes, and complex closures.
