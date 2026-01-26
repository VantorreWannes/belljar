# belljar 🫙

**Conditional memoization for complex runtime state.**

Standard decorators check the cache *before* execution. `belljar` lets you check the cache *during* execution.

By calling `include()`, you update the hash with runtime state (like file handles or database cursors). If `belljar` detects that this specific state has been processed before, **execution stops immediately** and the cached result is returned.

## Usage

```python

@belljar.store
def parse_log(file_handle):
    # 1. State is initially just the function args.
    
    # 2. Add runtime state to the hash (e.g., file cursor position).
    belljar.include(file_handle)

    # CHECKPOINT: 
    # If this exact sequence (args + file state) exists in the cache,
    # execution STOPS here and returns the stored value.
    belljar.check()
    
    print("Heavy processing...")
    return file_handle.read()
```

## Features

- **Mid-Execution Cache Hits:** Skip the heavy lifting if the intermediate state is recognized.
- **Complex Serialization:** Uses `dill` instead of `pickle`, supporting lambdas, local classes, and closures.
- **Zero Config:** caches to `.jar/` by default, or pass a path: `@store(Path("/tmp/cache"))`.

## Installation

```bash
uv add belljar
# or
pip install belljar
```
