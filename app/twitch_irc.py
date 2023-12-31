from __future__ import annotations
import abc
import pydantic

import websockets


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



class TwitchMessage:
    @classmethod
    @abc.abstractmethod
    def from_raw_message(cls, message: str, tags: dict[str, str] | None = None) -> TwitchMessage:
        raise NotImplementedError


class GlobalUserStateMessage(TwitchMessage):
    @classmethod
    @abc.abstractmethod
    def from_raw_message(cls, message: str, tags: dict[str, str] | None = None) -> GlobalUserStateMessage:
        pass


class PrivateMessage(TwitchMessage):
    # Bit events come in as a private message, checks the tags (I guess)
    # https://github.com/BarryCarlyon/twitch_misc/blob/8f38fce1c737d144b6cb7cb8bf71a417c28470b7/chat/eventbased/chat_template.js#L295
    @classmethod
    @abc.abstractmethod
    def from_raw_message(cls, message: str, tags: dict[str, str] | None = None) -> PrivateMessage:
        pass


class JoinMessage(TwitchMessage):
    @classmethod
    @abc.abstractmethod
    def from_raw_message(cls, message: str, tags: dict[str, str] | None = None) -> JoinMessage:
        pass


# PING :tmi.twitch.tv
# message loop
# :tmi.twitch.tv 001 cannibaljeebus :Welcome, GLHF!
# :tmi.twitch.tv 002 cannibaljeebus :Your host is tmi.twitch.tv
# :tmi.twitch.tv 003 cannibaljeebus :This server is rather new
# :tmi.twitch.tv 004 cannibaljeebus :-
# :tmi.twitch.tv 375 cannibaljeebus :-
# :tmi.twitch.tv 372 cannibaljeebus :You are in a maze of twisty passages, all alike.
# :tmi.twitch.tv 376 cannibaljeebus :>
# :tmi.twitch.tv CAP * ACK :twitch.tv/tags twitch.tv/commands twitch.tv/membership
# Origin[cannibaljeebus.tmi.twitch.tv] Command[353]: cannibaljeebus = #thebobbyv :cannibaljeebus
# Origin[cannibaljeebus.tmi.twitch.tv] Command[366]: cannibaljeebus #thebobbyv :End of /NAMES list
# MESSAGE: 
# @badge-info=subscriber/20;badges=vip/1,subscriber/18,bits/1000;color=#670070;display-name=Ginauz;emotes=;first-msg=0;flags=;id=575a24ac-0a91-48fb-b815-d62e0758c3e5;mod=0;returning-chatter=0;room-id=477536370;subscriber=1;tmi-sent-ts=1697759493254;turbo=0;user-id=73138589;user-type=;vip=1 :ginauz!ginauz@ginauz.tmi.twitch.tv PRIVMSG #thebobbyv :But the intro killed me as a first fallout game this man is zzzz
# @badge-info=subscriber/2;badges=vip/1,subscriber/2,bits/1;color=#FF4500;display-name=CannibalJeebus;emote-sets=0,14327,14415,19194,100675,163459,202264,865926,1554517,300206295,300374282,300548756,301592777,301850800,302281643,302656409,304089636,304230584,304230585,335211949,335835868,349692147,366129205,381795912,390635807,411369090,413457205,415785940,417199684,432107365,432588907,456899168,472873131,477339272,485611183,488737509,493057151,493728383,537206155,564265402,582929904,592920959,610186276,633714819,776769231,826004544,882819835,996603218,1127843598,1420623209,1447516779,1479080590,1714878156,1723224679,1832730947,1866292107,2058695649,2099632885,1c88d134-7982-4a5b-ab05-ff8680ab3805,316c713d-8f8a-4e76-86da-ac1caa24648a,36237fd7-c0b9-49d7-8731-89cc902c3091,4472a434-2cfc-47a8-98b3-aa099ffda1d5,4fa36322-02c6-49d0-be8a-0c42436a7725,5165cbf2-44f1-4f98-93ad-6d54f37abca8,66cbb53f-d712-45ac-8e4d-9b790b3be3a7,a24f6192-1ec6-44d7-a76d-b492d35f13a6,a24f6192-1ec6-44d7-a76d-b492d35f13a6,be6edcd9-71e9-4664-b8fb-524f26495d83,cbc996b7-31e4-46bd-8d86-379c55ff472e,dd8cbe57-6264-466e-9f63-97aaa7483004;mod=0;subscriber=1;user-type= :tmi.twitch.tv USERSTATE #thebobbyv
# @emote-only=0;followers-only=-1;r9k=0;room-id=477536370;slow=0;subs-only=0 :tmi.twitch.tv ROOMSTATE #thebobbyv

# JOIN
# :isnicable!isnicable@isnicable.tmi.twitch.tv JOIN #thebobbyv

# Origin[armeijasta!armeijasta@armeijasta.tmi.twitch.tv] Command[JOIN]: #thebobbyv
# :nirbing!nirbing@nirbing.tmi.twitch.tv JOIN #thebobbyv
# :mitchconnors!mitchconnors@mitchconnors.tmi.twitch.tv JOIN #thebobbyv
# :shadowollf!shadowollf@shadowollf.tmi.twitch.tv JOIN #thebobbyv
# :maybezita!maybezita@maybezita.tmi.twitch.tv JOIN #thebobbyv
# :lurxx!lurxx@lurxx.tmi.twitch.tv JOIN #thebobbyv
# :seanvinez1!seanvinez1@seanvinez1.tmi.twitch.tv JOIN #thebobbyv
# :drapsnatt!drapsnatt@drapsnatt.tmi.twitch.tv JOIN #thebobbyv


class TwitchIRC:
    def __init__(self, twitch_username: str, access_token: str, twitch_ws_uri: str | None = None) -> None:
        self.access_token = access_token
        self.twitch_username = twitch_username
        self.twitch_ws_uri = twitch_ws_uri or "wss://irc-ws.chat.twitch.tv:443"
    
    def parse_tags(self, raw_tags: str) -> dict[str, str]:
        return dict(tag.split('=') for tag in raw_tags.split(';'))
    

    def parse_raw_message(self, message: str) -> TwitchMessage:
        result = RawMessage.parse_raw_message(message)

        for r in result:
            print(f"[{r.command}] {r.message}")
    
    async def connect(self) -> None:
        async with websockets.connect(self.twitch_ws_uri) as websocket:
            try:
                await websocket.send(f"PASS oauth:{self.access_token}")
                await websocket.send(f"NICK {self.twitch_username}")
            except websockets.exceptions.ConnectionClosed as e:
                raise TwitchIRCAuthenticationException from e

            await websocket.send("CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership")
            await websocket.send("JOIN #thebobbyv")

            while True:
                try:
                    message = await websocket.recv()
                    self.parse_raw_message(message)
                except websockets.exceptions.ConnectionClosed:
                    break

    async def on_ping(self) -> None:
        pass

    async def on_message(self) -> None:
        pass

    async def on_join(self) -> None:
        pass

    async def on_part(self) -> None:
        pass

# async def hello():
#     uri = "ws://localhost:8765"
#     async with websockets.connect(uri) as websocket:
#         name = input("What's your name? ")

#         await websocket.send(name)
#         print(f">>> {name}")

#         greeting = await websocket.recv()
#         print(f"<<< {greeting}")

# if __name__ == "__main__":
#     asyncio.run(hello())
