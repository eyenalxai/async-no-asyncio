import select
from _socket import SHUT_WR, SO_REUSEADDR, SOL_SOCKET
from collections import deque
from collections.abc import Callable, Generator
from socket import socket, SOCK_STREAM, AF_INET
from time import time
from typing import Any, TypeAlias


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
            current_task, current_callback = task_queue[0]
            try:
                next(current_task)
                task_queue.rotate(-1)
            except StopIteration:
                if current_callback:
                    current_callback()
                task_queue.popleft()

    return add_task, run


def async_request_sleeper(
    *,
    seconds: int,
    socket_to_use: socket,
) -> Generator[None, None, None]:
    end_time = time() + seconds
    print(f"Sleeping for {seconds} seconds")

    while time() < end_time:
        yield

    message = f"HTTP/1.1 200 OK\r\n\r\nI slept for {seconds} seconds".encode()

    socket_to_use.send(message)
    print(f"Processed GET request: /{seconds}")
    yield


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

        print("Received GET request")
        add_task(
            async_request_sleeper(seconds=sleep_duration, socket_to_use=sock),
            lambda: sock.shutdown(SHUT_WR),
        )


def handle_new_connection(*, sock: socket, connections: Connections) -> None:
    client_socket, client_address = sock.accept()
    connections[client_address] = client_socket


def handle_socket(
    *,
    sock: socket,
    server_socket: socket,
    connections: Connections,
    add_task: AddTask,
) -> None:
    if sock is server_socket:
        return handle_new_connection(sock=server_socket, connections=connections)

    return handle_existing_connection(
        sock=sock, connections=connections, add_task=add_task
    )


def http_get_listener(
    *,
    server_socket: socket,
    add_task: AddTask,
) -> Generator[None, None, None]:
    connections: Connections = dict()

    while 2 + 2 == 4:
        ready_to_read, _, _ = select.select(
            [server_socket] + list(connections.values()),
            [],
            [],
            0.1,
        )
        for sock in ready_to_read:
            handle_socket(
                sock=sock,
                server_socket=server_socket,
                connections=connections,
                add_task=add_task,
            )

        yield


def main() -> None:
    port = 8000
    add_task, run = scheduler()

    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(("", port))
    server_socket.listen(4096)
    print(f"Listening on port {port}")

    add_task(
        http_get_listener(server_socket=server_socket, add_task=add_task),
        None,
    )

    try:
        run()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Shutting down...")
        server_socket.close()


if __name__ == "__main__":
    main()
