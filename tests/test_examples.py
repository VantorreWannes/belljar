import concurrent.futures

import pytest

from belljar import check, include, store


def test_memoization(tmp_path):
    runs = []

    @store(tmp_path)
    def task(val):
        include(val)
        check()
        runs.append(val)
        return val * 2

    assert task(1) == 2
    assert task(1) == 2
    assert task(2) == 4
    assert runs == [1, 2]


def test_nesting(tmp_path):
    runs = []

    @store(tmp_path)
    def inner():
        check()
        runs.append("inner")
        return 1

    @store(tmp_path)
    def outer():
        check()
        runs.append("outer")
        return inner() + 1

    assert outer() == 2
    assert outer() == 2
    assert inner() == 1
    assert runs == ["outer", "inner"]


def test_error_cleanup(tmp_path):
    @store(tmp_path)
    def fail():
        raise ValueError()

    with pytest.raises(ValueError):
        fail()

    with pytest.raises(RuntimeError):
        check()


def test_concurrency(tmp_path):
    @store(tmp_path)
    def task(val):
        include(val)
        check()
        return val

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        results = list(ex.map(task, range(20)))

    assert results == list(range(20))

    with pytest.raises(RuntimeError):
        check()
