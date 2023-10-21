import asyncio

from async_openai import OpenAI
import pydantic

from app.twitch_irc import PrivateMessage, SendMessage


class HistoricalMessage(pydantic.BaseModel):
    message: str
    response: str


class LRUCache:
    def __init__(self, count: int) -> None:
        self.count = count
        self.cache = []
    
    def add(self, item: HistoricalMessage) -> None:
        if len(self.cache) >= self.count:
            self.cache.pop(0)

        self.cache.append(item)



class OpenAIChat:
    SYSTEM_PROMPT = "You are a rude human chatter in a chat room who responds to {}. You are rude and abuse anyone who talks to you. You speak tersely."

    def __init__(self) -> None:
        self.message_history: dict[str, LRUCache] = {}
        self.cache_size = 10

    async def generate_response(self, username: str, message: str) -> str:
        cache = self.message_history.setdefault(username, LRUCache(self.cache_size))
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT.format(username)}]

        for item in cache.cache:
            messages.extend([
                {"role": "user", "content": item.message},
                {"role": "assistant", "content": item.response},
            ])
        
        messages.append({"role": "user", "content": message})

        # Send the request to OpenAI
        result = await OpenAI.async_chat_create(
            messages=messages,
            temperature=0.9,
        )

        content = result.messages[0].content

        # add the message to the cache
        cache.add(
            HistoricalMessage(
                message=message, 
                response=content,
            )
        )

        return f"@{username} {content}"


class AI:
    def __init__(
        self,
        response_aliases: list[str],
        send_queue: asyncio.Queue,
        message_queue: asyncio.Queue,
        flag: asyncio.Event,
        openai: OpenAI,
    ) -> None:
        self.send_queue = send_queue
        self.message_queue = message_queue
        self.flag = flag
        self.openai = openai
        self.response_aliases = [alias.lower() for alias in response_aliases]
        self.openai_chat = OpenAIChat()

    async def process_messages(self) -> None:
        while not self.flag.is_set():
            message: PrivateMessage = await self.message_queue.get()
            text_message = message.message.lower()

            # If the message contains an @{response_username} or the alias,
            # then we should respond to it.
            if any(alias in text_message for alias in self.response_aliases):
                if '@' in text_message:
                    text_message = text_message.replace('@', '')
            
                response = await self.openai_chat.generate_response(message.username, text_message)
                
                # Slap it in the queue
                await self.send_queue.put(
                    SendMessage(
                        channel=message.channel,
                        message=response,
                    )
                )
