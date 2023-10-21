from __future__ import annotations
import abc
import asyncio

import pydantic
import websockets


class SendMessage(pydantic.BaseModel):
    channel: str
    message: str


class TwitchIRCException(Exception):
    pass


class TwitchIRCAuthenticationException(TwitchIRCException):
    pass


class RawMessage(pydantic.BaseModel):
    tags: dict[str, str] | None
    origin: str | None
    command: str
    message: str

    @classmethod
    def parse_tags(cls, raw_tags: str) -> dict[str, str]:
        return dict(tag.split('=') for tag in raw_tags.split(';'))

    @classmethod
    def parse_raw_message(cls, message) -> list[RawMessage]:
        messages = message.split('\r\n')

        return [
            cls.parse_individual_raw_message(message)
            for message in messages if message
        ]

    @classmethod
    def parse_individual_raw_message(cls, message: str) -> RawMessage:
        message = message.strip()
        origin = None
        tags = None

        if message.startswith('@'):
            raw_tags, message = message.split(' ', 1)
            tags = cls.parse_tags(raw_tags[1:])

        if message.startswith(':'):
            origin, command_message = (
                message
                    .removeprefix(':')
                    .split(' ', 1)
            )

            command, message = command_message.split(' ', 1)
        else: # Ping, mostly
            command, message = message.split(':', 1)

        return cls(
            tags=tags,
            origin=origin,
            command=command.strip(),
            message=message.strip(),
        )


class TwitchMessage(pydantic.BaseModel):
    """
    Represents a message from Twitch
    """
    command: str

    @classmethod
    @abc.abstractmethod
    def from_raw_message(cls, message: RawMessage) -> TwitchMessage:
        raise NotImplementedError

    @staticmethod
    def parse_username(origin: str) -> str:
        return origin.split('!')[0]


class TaggedMessage(TwitchMessage):
    tags: dict[str, str]


class StateMessage(TaggedMessage):
    channel: str

    @classmethod
    def from_raw_message(cls, message: RawMessage) -> UserStateMessage:
        return cls(
            tags=message.tags,
            command=message.command,
            channel=message.message.lstrip('#'),
        )


# class GlobalUserStateMessage(TaggedMessage):
#     @classmethod
#     @abc.abstractmethod
#     def from_raw_message(cls, message: RawMessage) -> GlobalUserStateMessage:
#         pass


class UserStateMessage(StateMessage):
    pass


class RoomStateMessage(StateMessage):
    pass
        

class PrivateMessage(TaggedMessage):
    username: str
    channel: str
    message: str

    # Bit events come in as a private message, checks the tags (I guess)
    # https://github.com/BarryCarlyon/twitch_misc/blob/8f38fce1c737d144b6cb7cb8bf71a417c28470b7/chat/eventbased/chat_template.js#L295
    @classmethod
    def from_raw_message(cls, message: RawMessage) -> PrivateMessage:
        channel, chat_message = (
            message
                .message
                .lstrip('#')
                .split(' :', 1)
        )

        return cls(
            tags=message.tags,
            username=cls.parse_username(message.origin),
            channel=channel,
            message=chat_message,
            command=message.command,
        )


class ChannelEventMessage(TwitchMessage):
    """
    Messages with commands such as JOIN, PART 
    """
    channel: str
    username: str

    @classmethod
    def from_raw_message(cls, message: RawMessage) -> JoinMessage:
        return cls(
            channel=message.message.rstrip('#'),
            username=cls.parse_username(message.origin),
            command=message.command,
        )


class JoinMessage(ChannelEventMessage):
    pass


class PartMessage(ChannelEventMessage):
    pass


class PingMessage(TwitchMessage):
    message: str

    @classmethod
    def from_raw_message(cls, message: RawMessage) -> JoinMessage:
        return cls(
            command=message.command,
            message=message.message,
        )



CLASS_COMMAND_MAPPING = {
    'JOIN': JoinMessage,
    'PART': PartMessage,
    'PING': PingMessage,
    'PRIVMSG': PrivateMessage,
    'USERSTATE': UserStateMessage,
    'ROOMSTATE': RoomStateMessage,
}


class TwitchIRC:
    def __init__(
        self, 
        twitch_username: str, 
        access_token: str,
        channels: list[str],
        send_queue: asyncio.Queue,
        message_queue: asyncio.Queue,
        flag: asyncio.Event,
        twitch_ws_uri: str | None = None,
     ) -> None:
        self.access_token = access_token
        self.twitch_username = twitch_username.lower()
        self.channels = channels
        self.twitch_ws_uri = twitch_ws_uri or "wss://irc-ws.chat.twitch.tv:443"
        self.send_queue = send_queue
        self.message_queue = message_queue
        self.flag = flag

        self.function_mapping = {
            PrivateMessage: self.on_message,
            UserStateMessage: self.on_user_state,
            RoomStateMessage: self.on_room_state,
            JoinMessage: self.on_join,
            PartMessage: self.on_part,
            PingMessage: self.on_ping,
        }

    
    def parse_tags(self, raw_tags: str) -> dict[str, str]:
        return dict(tag.split('=') for tag in raw_tags.split(';'))
    
    def parse_raw_message(self, message: str) -> list[TwitchMessage]:
        messages: list[RawMessage] = RawMessage.parse_raw_message(message)
        ret = []

        for message in messages:
            Message: type[TwitchMessage] = CLASS_COMMAND_MAPPING.get(message.command)

            if not Message:
                continue

            ret.append(
                Message.from_raw_message(
                    message,
                )
            )

        return ret
    
    async def send_pong(self, websocket: websockets.WebSocketClientProtocol, message: str) -> None:
        await websocket.send(f"PONG {message}")
    
    async def send_private_message(self, websocket: websockets.WebSocketClientProtocol, channel: str, message: str) -> None:
        await websocket.send(f"PRIVMSG #{channel} :{message}")

    async def receive_messages(self, websocket: websockets.WebSocketClientProtocol) -> None:
        while not self.flag.is_set():
            try:
                messages = self.parse_raw_message(await websocket.recv())

                for message in messages:
                    fn = self.function_mapping.get(type(message))

                    if not fn:
                        continue

                    await fn(websocket, message)

            except websockets.exceptions.ConnectionClosed:
                break
    
    async def process_send_queue(self, websocket: websockets.WebSocketClientProtocol) -> None:
        while not self.flag.is_set():
            message: SendMessage = await self.send_queue.get()

            await self.send_private_message(
                websocket,
                message.channel,
                message.message,
            )

    async def run(self) -> None:
        async with websockets.connect(self.twitch_ws_uri) as websocket:
            try:
                await websocket.send(f"PASS oauth:{self.access_token}")
                await websocket.send(f"NICK {self.twitch_username}")
            except websockets.exceptions.ConnectionClosed as e:
                raise TwitchIRCAuthenticationException from e

            await websocket.send("CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership")
            
            for channel in self.channels:
                await websocket.send(f"JOIN #{channel}")

            # Example join on the event
            # await event.wait()
            await asyncio.gather(
                self.receive_messages(websocket),
                self.process_send_queue(websocket),
            )

    async def on_ping(self, websocket: websockets.WebSocketClientProtocol, message: PingMessage) -> None:
        await self.send_pong(websocket, message.message)

    async def on_message(self, websocket: websockets.WebSocketClientProtocol, message: PrivateMessage) -> None:
        if message.username.lower() == self.twitch_username:
            return
        
        await self.message_queue.put(message)

    async def on_join(self, websocket: websockets.WebSocketClientProtocol, message: JoinMessage) -> None:
        pass

    async def on_part(self, websocket: websockets.WebSocketClientProtocol, message: PartMessage) -> None:
        pass

    async def on_user_state(self, websocket: websockets.WebSocketClientProtocol, message: UserStateMessage) -> None:
        pass

    async def on_room_state(self, websocket: websockets.WebSocketClientProtocol, message: RoomStateMessage) -> None:
        pass
