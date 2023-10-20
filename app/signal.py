import asyncio


e = asyncio.Event()

# class Signal(asyncio.Event):
#     def __init__(self, *args, **kwargs) -> None:
#         super().__init__(*args, **kwargs)

#         if not self._loop:
#             self._loop = self._get_loop()

#     def set(self):
#         self._loop.call_soon_threadsafe(super().set)

#     def clear(self):
#         self._loop.call_soon_threadsafe(super().clear)
