# jar 🫙

**Reliable caching for complex Python code.**

Standard caching decorators often break when dealing with class methods, lambdas, or open files.

`jar` solves this by letting you verify the cache *inside* the function. Instead of guessing dependencies from arguments, you declare them explicitly with `needs()`.

This allows you to checkpoint execution based on runtime state—like an open file handle or a database cursor—and exit early if that specific state has been processed before. Because it uses `dill`, it supports closures and local classes out of the box.

## Usage

Use `needs()` to update the cache signature. If `jar` recognizes the sequence of code, arguments, and `needs`, it stops execution and returns the stored result.

```python
import jar

class Parser:
    def __init__(self, mode):
        self.mode = mode

    @jar.preserve
    def process(self, file_handle):
        # Hash the file handle's current state (cursor, mode, etc).
        # 'self' and function args are included automatically.
        jar.needs(file_handle)

        # CHECKPOINT: 
        # If this exact state exists in the cache, we stop here.
        print("Parsing...") 
        return file_handle.read()

p = Parser(mode="strict")

# 1. Runs logic ("Parsing...")
with open("data.txt", "r") as f:
    p.process(f) 

# 2. File handle is fresh, but state is identical -> Returns cache
with open("data.txt", "r") as f:
    p.process(f)
```
