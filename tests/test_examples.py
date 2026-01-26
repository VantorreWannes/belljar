from belljar import check, include, store


def test_runs(tmp_path):
    ran = False

    @store(tmp_path)
    def task():
        nonlocal ran
        ran = True
        return 10

    assert task() == 10
    assert ran


def test_skips(tmp_path):
    runs = 0

    @store(tmp_path)
    def task():
        nonlocal runs
        check()
        runs += 1
        return 10

    task()
    task()

    assert runs == 1


def test_varies(tmp_path):
    runs = 0

    @store(tmp_path)
    def task(val):
        nonlocal runs
        include(val)
        check()
        runs += 1

    task("a")
    task("b")

    assert runs == 2
