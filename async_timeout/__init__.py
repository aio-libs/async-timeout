import asyncio
import sys

from types import TracebackType
from typing import Optional, Type, Any  # noqa
from typing_extensions import final


__version__ = '3.0.1'


@final
class timeout:
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> with timeout(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    timeout - value in seconds or None to disable timeout logic
    loop - asyncio compatible event loop
    """
    @classmethod
    def at(cls, when: float) -> 'timeout':
        """Schedule the timeout at absolute time.

        when arguments points on the time in the same clock system
        as loop.time().

        Please note: it is not POSIX time but a time with
        undefined starting base, e.g. the time of the system power on.

        """
        ret = cls(None)
        ret._cancel_at = when
        return ret

    def __init__(self, timeout: Optional[float],
                 *, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._delay = timeout
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._task = None  # type: Optional[asyncio.Task[Any]]
        self._cancelled = False
        self._cancel_handler = None  # type: Optional[asyncio.Handle]
        self._cancel_at = None  # type: Optional[float]
        self._started_at = None  # type: Optional[float]
        self._exited_at = None  # type: Optional[float]

    def __enter__(self) -> 'timeout':
        return self._do_enter()

    def __exit__(self,
                 exc_type: Type[BaseException],
                 exc_val: BaseException,
                 exc_tb: TracebackType) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    async def __aenter__(self) -> 'timeout':
        return self._do_enter()

    async def __aexit__(self,
                        exc_type: Type[BaseException],
                        exc_val: BaseException,
                        exc_tb: TracebackType) -> None:
        self._do_exit(exc_type)

    @property
    def expired(self) -> bool:
        """Is timeout expired during execution?"""
        return self._cancelled

    @property
    def remaining(self) -> Optional[float]:
        """Number of seconds remaining to the timeout expiring."""
        if self._cancel_at is None:
            return None
        elif self._exited_at is None:
            return max(self._cancel_at - self._loop.time(), 0.0)
        else:
            return max(self._cancel_at - self._exited_at, 0.0)

    @property
    def elapsed(self) -> float:
        """Number of elapsed seconds.

        The time is counted starting from entering into
        the timeout context manager.

        """
        if self._started_at is None:
            return 0.0
        elif self._exited_at is None:
            return self._loop.time() - self._started_at
        else:
            return self._exited_at - self._started_at

    def _do_enter(self) -> 'timeout':
        # Support Tornado 5- without timeout
        # Details: https://github.com/python/asyncio/issues/392
        if self._delay is None and self._cancel_at is None:
            return self

        self._task = _current_task(self._loop)
        if self._task is None:
            raise RuntimeError('Timeout context manager should be used '
                               'inside a task')

        self._started_at = self._loop.time()

        if self._delay is not None:
            # relative timeout mode
            if self._delay <= 0:
                self._loop.call_soon(self._cancel_task)
                return self

            self._cancel_at = self._started_at + self._delay
        else:
            # absolute timeout
            assert self._cancel_at is not None

        self._cancel_handler = self._loop.call_at(
            self._cancel_at, self._cancel_task)
        return self

    def _do_exit(self, exc_type: Type[BaseException]) -> None:
        self._exited_at = self._loop.time()
        if exc_type is asyncio.CancelledError and self._cancelled:
            self._cancel_handler = None
            self._task = None
            raise asyncio.TimeoutError
        if self._cancel_handler is not None:
            self._cancel_handler.cancel()
            self._cancel_handler = None
        self._task = None
        return None

    def _cancel_task(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._cancelled = True


def _current_task(loop: asyncio.AbstractEventLoop) -> 'asyncio.Task[Any]':
    if sys.version_info >= (3, 7):
        return asyncio.current_task(loop=loop)
    else:
        return asyncio.Task.current_task(loop=loop)
