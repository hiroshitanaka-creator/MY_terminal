import asyncio
import fcntl
import os
import struct
import termios
from typing import Callable, Awaitable

import ptyprocess


class PTYSession:
    def __init__(self):
        self._proc: ptyprocess.PtyProcess | None = None
        self._task: asyncio.Task | None = None

    async def start(
        self,
        shell: str,
        on_output: Callable[[bytes], Awaitable[None]],
        cols: int = 80,
        rows: int = 24,
    ):
        self._proc = ptyprocess.PtyProcess.spawn(
            [shell],
            dimensions=(rows, cols),
        )
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._read_loop(on_output))

    async def _read_loop(self, on_output: Callable[[bytes], Awaitable[None]]):
        loop = asyncio.get_event_loop()
        while self._proc and self._proc.isalive():
            try:
                data = await loop.run_in_executor(None, self._read_chunk)
                if data:
                    await on_output(data)
            except EOFError:
                break
            except Exception:
                break

    def _read_chunk(self) -> bytes:
        if self._proc is None:
            return b""
        try:
            return self._proc.read(4096)
        except EOFError:
            return b""

    def write(self, data: bytes):
        if self._proc and self._proc.isalive():
            self._proc.write(data)

    def resize(self, rows: int, cols: int):
        if self._proc and self._proc.isalive():
            self._proc.setwinsize(rows, cols)

    async def kill(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._proc and self._proc.isalive():
            self._proc.terminate(force=True)
