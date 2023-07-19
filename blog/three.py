from collections import deque
from collections.abc import Callable, Generator
from time import time
from typing import TypeAlias


AddTask: TypeAlias = Callable[[Generator], None]
Run: TypeAlias = Callable[[], None]
Scheduler: TypeAlias = tuple[AddTask, Run]


def scheduler() -> Scheduler:
    task_queue: deque = deque([], maxlen=200)

    def add_task(generator: Generator) -> None:
        task_queue.append(generator)

    def run() -> None:
        while task_queue:
            current_task = task_queue[0]
            try:
                next(current_task)
                task_queue.rotate(-1)
            except StopIteration:
                task_queue.popleft()

    return add_task, run


def async_sleep(*, seconds: int) -> Generator[None, None, None]:
    print(f"Task sleeping for {seconds} seconds started")

    end_time = time() + seconds

    while time() < end_time:
        yield

    print(f"Task sleeping for {seconds} seconds finished")
    yield


def main() -> None:
    add_task, run = scheduler()

    add_task(async_sleep(seconds=4))
    add_task(async_sleep(seconds=3))
    add_task(async_sleep(seconds=2))
    add_task(async_sleep(seconds=1))

    run()


if __name__ == "__main__":
    main()
