from collections import deque
from collections.abc import Callable, Generator
from time import time
from typing import TypeAlias, Any


Callback: TypeAlias = Callable[[], Any]
AddTask: TypeAlias = Callable[[Generator[Any, Any, Any], Callback | None], None]
Run: TypeAlias = Callable[[], None]
Scheduler: TypeAlias = tuple[AddTask, Run]


def scheduler() -> Scheduler:
    task_queue: deque = deque([], maxlen=200)

    def add_task(generator: Generator, callback: Callback | None = None) -> None:
        task_queue.append((generator, callback))

    def run() -> None:
        while task_queue:
            current_task, current_callback = task_queue[0]
            try:
                next(current_task)
                task_queue.rotate(-1)
            except StopIteration:
                if current_callback:
                    current_callback()
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

    add_task(
        async_sleep(seconds=1),
        lambda: add_task(
            async_sleep(seconds=1),
            lambda: add_task(
                async_sleep(seconds=1),
                lambda: add_task(
                    async_sleep(seconds=1),
                    lambda: add_task(
                        async_sleep(seconds=1),
                        lambda: add_task(
                            async_sleep(seconds=1),
                            lambda: add_task(
                                async_sleep(seconds=1),
                                lambda: add_task(
                                    async_sleep(seconds=1),
                                    lambda: add_task(
                                        async_sleep(seconds=1),
                                        None,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),

    run()


if __name__ == "__main__":
    main()
