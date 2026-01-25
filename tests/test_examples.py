import belljar


def test_checkpoint(tmp_path):
    trace = []

    @belljar.jar(tmp_path)
    def run(data):
        trace.append("setup")
        belljar.includes(data)
        trace.append("work")
        return "done"

    run("v1")
    run("v1")

    assert trace == ["setup", "work", "setup"]


def test_lambdas(tmp_path):
    @belljar.jar(tmp_path)
    def adder(n):
        belljar.includes(n)
        return lambda x: x + n

    assert adder(10)(5) == 15

    assert adder(10)(5) == 15
