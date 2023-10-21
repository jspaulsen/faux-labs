import asyncio

from app.config import Configuration
from app.twitch_irc import TwitchIRC

from app.ai import AI


async def main():
    configuration = Configuration()
    send_queue = asyncio.Queue()
    message_queue = asyncio.Queue()
    flag = asyncio.Event()

    client = TwitchIRC(
        configuration.twitch_username,
        configuration.twitch_oauth_token,
        channels=[configuration.twitch_username],
        send_queue=send_queue,
        message_queue=message_queue,
        flag=flag,
    )

    ai = AI(
        [configuration.twitch_username, 'cannibal'],
        send_queue,
        message_queue,
        flag,
        configuration.openai_api_key,
    )

    while True:
        await asyncio.gather(
            client.run(),
            ai.process_messages(),
        )

    # ai should have sentiment for particular users, defaulting to unpositive

if __name__ == '__main__':
    asyncio.run(main())
