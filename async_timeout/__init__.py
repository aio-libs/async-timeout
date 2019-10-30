import asyncio
import sys

from types import TracebackType
from typing import Any, Optional, Type
from typing_extensions import final


__version__ = '4.0.0a0'


def timeout(delay: Optional[float]) -> 'Timeout':
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> with timeout(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    delay - value in seconds or None to disable timeout logic
    """
    loop = _get_running_loop()
    if delay is not None:
        when = loop.time() + delay  # type: Optional[float]
    else:
        when = None
    return Timeout(when, loop)


def timeout_at(when: Optional[float]) -> 'Timeout':
    """Schedule the timeout at absolute time.

    when arguments points on the time in the same clock system
    as loop.time().

    Please note: it is not POSIX time but a time with
    undefined starting base, e.g. the time of the system power on.
    """
    loop = _get_running_loop()
    return Timeout(when, loop)


@final
class Timeout:
    # Internal class, please don't instantiate it directly
    # Use timeout() and timeout_at() public factories instead.

    def __init_subclass__(cls: Type['Timeout']) -> None:
        raise TypeError("Inheritance class {} from timeout "
                        "is forbidden".format(cls.__name__))

    def __init__(
            self,
            when: Optional[float],
            loop: asyncio.AbstractEventLoop
    ) -> None:
        now = loop.time()
        if when is not None:
            when = max(when, now)
        self._entered_at = now
        self._cancel_at = when
        self._loop = loop
        self._cancelled = False
        self._exited_at = None  # type: Optional[float]

        # Support Tornado<5.0 without timeout
        # Details: https://github.com/python/asyncio/issues/392

        if self._cancel_at is None:
            self._task = None  # type: Optional[asyncio.Task[Any]]
            self._cancel_handler = None  # type: Optional[asyncio.Handle]
        else:
            self._task = _current_task(self._loop)
            if self._task is None:
                raise RuntimeError('Timeout context manager should be used '
                                   'inside a task')

            self._cancel_handler = self._loop.call_at(
                self._cancel_at, self._on_timeout)

    def __enter__(self) -> 'Timeout':
        return self

    def __exit__(self,
                 exc_type: Type[BaseException],
                 exc_val: BaseException,
                 exc_tb: TracebackType) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    async def __aenter__(self) -> 'Timeout':
        return self

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
    def entered_at(self) -> float:
        return self._entered_at

    @property
    def exited_at(self) -> Optional[float]:
        return self._exited_at

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
        if self._exited_at is None:
            return self._loop.time() - self._entered_at
        else:
            return self._exited_at - self._entered_at

    def _do_exit(self, exc_type: Type[BaseException]) -> None:
        self._exited_at = self._loop.time()
        if exc_type is asyncio.CancelledError and self._cancelled:
            self._cancel_handler = None
            self._task = None
            raise asyncio.TimeoutError
        # timeout is not expired
        self.reject()
        self._task = None
        return None

    def reject(self) -> None:
        """Reject scheduled timeout if any."""
        # cancel is maybe better name but
        # task.cancel() raises CancelledError in asyncio world.
        if self._cancel_handler is not None:
            self._cancel_handler.cancel()
            self._cancel_handler = None

    def _on_timeout(self) -> None:
        if self._task is not None:
            self._task.cancel()
            self._cancelled = True


def _current_task(loop: asyncio.AbstractEventLoop) -> 'asyncio.Task[Any]':
    if sys.version_info >= (3, 7):
        return asyncio.current_task(loop=loop)
    else:
        return asyncio.Task.current_task(loop=loop)


def _get_running_loop() -> asyncio.AbstractEventLoop:
    return asyncio.get_event_loop()
