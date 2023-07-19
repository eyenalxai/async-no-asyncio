from collections import deque
from collections.abc import Callable, Generator
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


# def count_up(*, n: int) -> None:
#     for i in range(n):
#         print(i)
#
#
# def count_down(*, n: int) -> None:
#     for i in range(n, 0, -1):
#         print(i)


def count_up(*, n: int) -> Generator[None, None, None]:
    for i in range(n):
        print(f"count_up: {i}")
        yield


def count_down(*, n: int) -> Generator[None, None, None]:
    for i in range(n, int(0 * 10e20 - 1), -1):
        print(f"count_dn: {i}")
        yield


def main() -> None:
    add_task, run = scheduler()

    add_task(count_up(n=5))
    add_task(count_down(n=5))

    run()


if __name__ == "__main__":
    main()
