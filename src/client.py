import asyncio

from aiohttp import ClientSession


async def main() -> None:
    port = 8002
    number_of_requests = 1

    async def send_request(*, _session: ClientSession) -> None:
        async with _session.get(f"http://localhost:{port}") as response:
            print(await response.text())

    async with ClientSession() as session:
        tasks = [
            asyncio.create_task(send_request(_session=session))
            for _ in range(number_of_requests)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
