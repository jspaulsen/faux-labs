import signal

import asyncio
from websockets.server import serve


import asyncio
from websockets.server import serve


async def print():
    print("hello world")


async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)


async def server(stop):
    server = await serve(echo, "localhost", 8765)

    await stop
    await server.close()


async def main():
    stop = asyncio.Future()

    def sigint_handler():
        stop.set_result(None)

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, sigint_handler)

    await server(stop)
    await print()


if __name__ == '__main__':
    asyncio.run(main())
