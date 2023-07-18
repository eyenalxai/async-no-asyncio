import select
from _socket import SHUT_WR, SO_REUSEADDR, SOL_SOCKET
from collections import deque
from collections.abc import Callable, Generator
from socket import socket, SOCK_STREAM, AF_INET
from time import time
from typing import Any, TypeAlias

from config.const import PORT
from config.log import logger

Task: TypeAlias = Generator[Any, Any, Any]


Callback: TypeAlias = Callable[[], Any]
AddTask: TypeAlias = Callable[[Generator[Any, Any, Any], Callback | None], None]
Run: TypeAlias = Callable[[], None]
Scheduler: TypeAlias = tuple[AddTask, Run]

Connections: TypeAlias = dict[tuple[str, int], socket]


def scheduler() -> Scheduler:
    task_queue: deque = deque([], maxlen=200)

    def add_task(generator: Generator, callback: Callback | None = None) -> None:
        task_queue.append((generator, callback))

    def run() -> None:
        while task_queue:
            logger.debug(f"Task queue length: {len(task_queue)}")
            current_task, current_callback = task_queue[0]
            logger.debug(f"Current task: {current_task.__name__}")
            try:
                next(current_task)
            except StopIteration:
                logger.debug("Task finished")
                if current_callback:
                    current_callback()
                task_queue.popleft()
            else:
                task_queue.rotate(-1)

    return add_task, run


def async_sleeper(*, seconds: int) -> Generator[None, None, None]:
    end_time = time() + seconds
    logger.debug(f"Task sleeping for {seconds} seconds")

    while time() < end_time:
        yield

    logger.debug(f"Task finished sleeping for {seconds} seconds")
    yield


def async_request_sleeper(
    *,
    seconds: int,
    socket_to_use: socket,
) -> Generator[None, None, None]:
    end_time = time() + seconds
    logger.info(f"Sleeping for {seconds} seconds")

    while time() < end_time:
        yield

    logger.debug(f"Finished sleeping for {seconds} seconds")

    socket_to_use.send(b"HTTP/1.1 200 OK\r\n\r\noof!!")
    socket_to_use.shutdown(SHUT_WR)
    logger.info(f"Processed GET request: /{seconds}")
    yield


def handle_new_connection(*, sock: socket, connections: Connections) -> None:
    client_socket, client_address = sock.accept()
    connections[client_address] = client_socket


def handle_existing_connection(
    *,
    sock: socket,
    connections: Connections,
    add_task: AddTask,
) -> None:
    del connections[sock.getpeername()]

    request = sock.recv(1024)

    if request and b"GET" in request:
        uri = request.decode().split()[1]
        try:
            sleep_duration = int(uri.split("/")[-1])
        except ValueError:
            sleep_duration = 1

        logger.info("Received GET request")
        add_task(
            async_request_sleeper(seconds=sleep_duration, socket_to_use=sock), None
        )
        logger.debug("Added task to queue")


def handle_socket(
    *,
    sock: socket,
    listener_socket: socket,
    connections: Connections,
    add_task: AddTask,
) -> None:
    (sock is listener_socket) and handle_new_connection(
        sock=listener_socket, connections=connections
    )

    (sock is not listener_socket) and handle_existing_connection(
        sock=sock, connections=connections, add_task=add_task
    )


def http_get_listener(
    *,
    listener_socket: socket,
    add_task: AddTask,
) -> Generator[None, None, None]:
    connections: Connections = dict()

    while True:
        ready_to_read, _, _ = select.select(
            [listener_socket] + list(connections.values()),
            [],
            [],
            0.1,
        )
        for sock in ready_to_read:
            handle_socket(
                sock=sock,
                listener_socket=listener_socket,
                connections=connections,
                add_task=add_task,
            )

        yield


def main() -> None:
    add_task, run = scheduler()

    listener_socket = socket(AF_INET, SOCK_STREAM)
    listener_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listener_socket.bind(("", PORT))
    listener_socket.listen(4096)
    logger.info(f"Listening on port {PORT}")

    add_task(
        http_get_listener(listener_socket=listener_socket, add_task=add_task),
        None,
    )

    try:
        run()
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received. Shutting down...")
        listener_socket.close()


if __name__ == "__main__":
    main()
