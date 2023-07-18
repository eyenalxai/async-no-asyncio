import asyncio

from aiohttp import ClientSession

from config import PORT


async def main() -> None:
    number_of_requests = 100

    async def send_request(*, _session: ClientSession) -> None:
        async with _session.get(f"http://localhost:{PORT}") as response:
            print(await response.text())

    async with ClientSession() as session:
        tasks = [
            asyncio.create_task(send_request(_session=session))
            for _ in range(number_of_requests)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
