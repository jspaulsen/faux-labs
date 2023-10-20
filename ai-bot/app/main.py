import asyncio

from app.config import Configuration
from app.twitch_irc import TwitchIRC


async def main():
    configuration = Configuration()
    send_queue = asyncio.Queue()
    message_queue = asyncio.Queue()
    flag = asyncio.Event()

    client = TwitchIRC(
        configuration.twitch_username,
        configuration.twitch_oauth_token,
        send_queue=send_queue,
        message_queue=message_queue,
        flag=flag,
    )

    while True:
        await client.run()

    

    # ai should have sentiment for particular users, defaulting to unpositive

if __name__ == '__main__':
    asyncio.run(main())
