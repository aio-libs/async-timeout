import asyncio
import sys

from types import TracebackType
from typing import Any, Optional, Type
from typing_extensions import final


__version__ = '4.0.0a0'


__all__ = ('timeout', 'timeout_at')


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
    #
    # Implementation note: `async with timeout()` is preferred
    # over `with timeout()`.
    # While technically the Timeout class implementation
    # doesn't need to be async at all,
    # the `async with` statement explicitly points that
    # the context manager should be used from async function context.
    #
    # This design allows to avoid many silly misusages.

    def __init__(
            self,
            when: Optional[float],
            loop: asyncio.AbstractEventLoop
    ) -> None:
        now = loop.time()
        if when is not None:
            when = max(when, now)
        self._started_at = now
        self._timeout_at = when
        self._loop = loop
        self._expired = False
        self._finished_at = None  # type: Optional[float]

        # Support Tornado<5.0 without timeout
        # Details: https://github.com/python/asyncio/issues/392

        if self._timeout_at is None:
            self._timeout_handler = None  # type: Optional[asyncio.Handle]
        else:
            task = _current_task(self._loop)
            if task is None:
                raise RuntimeError('Timeout context manager should be used '
                                   'inside a task')

            self._timeout_handler = self._loop.call_at(
                self._timeout_at, self._on_timeout, task)

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
        return self._expired

    @property
    def started_at(self) -> float:
        return self._started_at

    @property
    def finished_at(self) -> Optional[float]:
        return self._finished_at

    @property
    def timeout_at(self) -> Optional[float]:
        return self._timeout_at

    def _do_exit(self, exc_type: Type[BaseException]) -> None:
        self._finished_at = self._loop.time()
        if exc_type is asyncio.CancelledError and self._expired:
            self._timeout_handler = None
            raise asyncio.TimeoutError
        # timeout is not expired
        self.reject()
        return None

    def reject(self) -> None:
        """Reject scheduled timeout if any."""
        # cancel is maybe better name but
        # task.cancel() raises CancelledError in asyncio world.
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

    def _on_timeout(self, task: 'asyncio.Task[None]') -> None:
        task.cancel()
        self._expired = True


def _current_task(loop: asyncio.AbstractEventLoop) -> 'asyncio.Task[Any]':
    if sys.version_info >= (3, 7):
        return asyncio.current_task(loop=loop)
    else:
        return asyncio.Task.current_task(loop=loop)


def _get_running_loop() -> asyncio.AbstractEventLoop:
    return asyncio.get_event_loop()
