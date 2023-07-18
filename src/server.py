import select
from _socket import SHUT_WR, SO_REUSEADDR, SOL_SOCKET
from collections import deque
from collections.abc import Callable, Generator
from socket import socket, SOCK_STREAM, AF_INET
from time import time
from typing import Any, TypeAlias

from config import PORT

Task: TypeAlias = Generator[Any, Any, Any]


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
            print(f"Task queue length: {len(task_queue)}")
            current_task, current_callback = task_queue[0]
            print(f"Current task: {current_task.__name__}")
            try:
                next(current_task)
            except StopIteration:
                print("Task finished")
                if current_callback:
                    current_callback()
                task_queue.popleft()
            else:
                task_queue.rotate(-1)

    return add_task, run


def async_sleeper(*, seconds: int) -> Generator[None, None, None]:
    end_time = time() + seconds
    print(f"Task sleeping for {seconds} seconds")

    while time() < end_time:
        yield

    print(f"Task finished sleeping for {seconds} seconds")


def handle_request(
    *,
    client_socket: socket,
    add_task: AddTask,
) -> Generator:
    request = client_socket.recv(1024)

    if b"GET" in request:
        print("Received GET request")
        add_task(async_request_sleeper(seconds=1, socket_to_use=client_socket), None)
        print("Added task to queue")

    yield


def http_get_listener(listener_socket, add_task):
    connections = {}

    while True:
        ready_to_read, _, _ = select.select(
            [listener_socket] + list(connections.values()), [], [], 0.1
        )
        for sock in ready_to_read:
            if sock is listener_socket:
                client_socket, client_address = listener_socket.accept()
                connections[client_address] = client_socket
            else:
                del connections[sock.getpeername()]
                request = sock.recv(1024)
                if request and b"GET" in request:
                    print("Received GET request")
                    add_task(async_request_sleeper(seconds=1, socket_to_use=sock), None)
                    print("Added task to queue")

        yield


def async_request_sleeper(
    *,
    seconds: int,
    socket_to_use: socket,
) -> Generator[None, None, None]:
    end_time = time() + seconds
    print(f"Sleeping for {seconds} seconds")

    while time() < end_time:
        yield

    print(f"Finished sleeping for {seconds} seconds")

    socket_to_use.send(b"HTTP/1.1 200 OK\r\n\r\noof!!")
    socket_to_use.shutdown(SHUT_WR)
    yield


def main() -> None:
    add_task, run = scheduler()

    listener_socket = socket(AF_INET, SOCK_STREAM)
    listener_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listener_socket.bind(("", PORT))
    listener_socket.listen(4096)
    print(f"Listening on port {PORT}")

    add_task(
        http_get_listener(listener_socket=listener_socket, add_task=add_task),
        None,
    )

    try:
        run()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")
        listener_socket.close()


if __name__ == "__main__":
    main()