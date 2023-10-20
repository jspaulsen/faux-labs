import json

import websockets


class TwitchPubSubClient:
    # https://dev.twitch.tv/docs/eventsub/handling-websocket-events/
    # wss://eventsub.wss.twitch.tv/ws
    # TODO: Accept a Future to stop the client
    def __init__(self, twitch_uri: str | None = None) -> None:
        self.twitch_urni = twitch_uri or "wss://pubsub-edge.twitch.tv"
    
    async def consumer(self, websocket: websockets.WebSocketClientProtocol) -> None:
        async for message in websocket:
            print(message)
            # await websocket.send(message)

    async def connect(self) -> None:
        async with websockets.connect(self.twitch_uri) as websocket:
            if websocket.open:
                print("Connection open")
                # chat_moderator_actions.*.44322889
                message = {"type": "LISTEN", "nonce": str("01234567"), "data":{"topics": ["chat_moderator_actions.*.44322889"], "auth_token": "px57alz6y4hhx5iziy0j04txvpeib4"}}
                await websocket.send(json.dumps(message))

            while True:
                print(await websocket.recv())
        # async with websockets.connect(self.twitch_uri) as websocket:
        #     await self.consumer(websocket)


# async def consumer_handler(websocket):
#     async for message in websocket:
#         await consumer(message)
