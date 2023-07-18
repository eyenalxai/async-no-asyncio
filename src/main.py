from collections.abc import Callable, Generator
from typing import Any


def task(generator: Generator) -> Callable[[], Any]:
    def runner() -> Any:
        return next(generator)

    return runner


def scheduler() -> (
    tuple[Callable[[Generator, Callable[[Any], Any]], None], Callable[[], None]]
):
    task_queue: list[tuple[Callable[[], Any], Callable[[], None]]] = []

    def add_task(generator: Generator, callback: Callable[[], Any]) -> None:
        task_queue.append((task(generator), callback))

    def run() -> None:
        while task_queue:
            current_task, current_callback = task_queue.pop(0)
            try:
                current_task()
                task_queue.append((current_task, current_callback))
            except StopIteration:
                current_callback()

    return add_task, run


def async_sleeper(*, seconds: int) -> Generator:
    end_time = time() + seconds
    print(f"Task sleeping for {seconds} seconds")

    while time() < end_time:
        yield

    print(f"Task finished sleeping for {seconds} seconds")


def main() -> None:
    add_task, run = scheduler()

    add_task(async_sleeper(seconds=1), lambda: print(f"Callback 1!"))
    add_task(async_sleeper(seconds=2), lambda: print(f"Callback 2!"))
    add_task(
        async_sleeper(seconds=3),
        lambda: add_task(
            async_sleeper(seconds=1),
            lambda: add_task(
                async_sleeper(seconds=1), lambda: print(f"Nested Callback!")
            ),
        ),
    )

    run()


if __name__ == "__main__":
    main()
