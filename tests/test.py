from jar import needs, preserve


def test_checkpoint(tmp_path):
    trace = []

    @preserve(tmp_path)
    def run(data):
        trace.append("setup")
        needs(data)
        trace.append("work")
        return "done"

    run("v1")
    run("v1")

    assert trace == ["setup", "work", "setup"]


def test_lambdas(tmp_path):
    @preserve(tmp_path)
    def adder(n):
        return lambda x: x + n

    assert adder(10)(5) == 15

    assert adder(10)(5) == 15
