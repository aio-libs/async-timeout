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

    >>> async with timeout(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    delay - value in seconds or None to disable timeout logic
    """
    loop = _get_running_loop()
    if delay is not None:
        deadline = loop.time() + delay  # type: Optional[float]
    else:
        deadline = None
    return Timeout(deadline, loop)


def timeout_at(deadline: Optional[float]) -> 'Timeout':
    """Schedule the timeout at absolute time.

    deadline arguments points on the time in the same clock system
    as loop.time().

    Please note: it is not POSIX time but a time with
    undefined starting base, e.g. the time of the system power on.

    >>> async with timeout_at(loop.time() + 10):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    """
    loop = _get_running_loop()
    return Timeout(deadline, loop)


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
    #
    # TimeoutError is raised immadiatelly when scheduled
    # if the deadline is passed.
    # The purpose is to time out as sson as possible
    # without waiting for the next await expression.

    __slots__ = ('_deadline', '_loop', '_expired', '_task', '_timeout_handler')

    def __init__(
            self,
            deadline: Optional[float],
            loop: asyncio.AbstractEventLoop
    ) -> None:
        self._loop = loop
        self._expired = False

        task = _current_task(self._loop)
        self._task = task

        self._timeout_handler = None  # type: Optional[asyncio.Handle]
        if deadline is None:
            self._deadline = None  # type: Optional[float]
        else:
            self.shift_at(deadline)

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
                        exc_tb: TracebackType) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    @property
    def expired(self) -> bool:
        """Is timeout expired during execution?"""
        return self._expired

    @property
    def deadline(self) -> Optional[float]:
        return self._deadline

    def reject(self) -> None:
        """Reject scheduled timeout if any."""
        # cancel is maybe better name but
        # task.cancel() raises CancelledError in asyncio world.
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

    def shift(self, delay: float) -> None:
        """Advance timeout on delay seconds.

        The delay can be negative.
        """
        if self._deadline is None:
            raise RuntimeError("shifting timeout without deadline")
        self.shift_at(self._deadline + delay)

    def shift_at(self, deadline: float) -> None:
        if self._expired:
            raise RuntimeError("cannot reschedule expired timeout")
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
        self._deadline = deadline
        now = self._loop.time()
        if deadline <= now:
            self._timeout_handler = None
            raise asyncio.TimeoutError
        self._timeout_handler = self._loop.call_at(
            deadline,
            self._on_timeout,
            self._task
        )

    def _do_exit(self, exc_type: Type[BaseException]) -> None:
        if exc_type is asyncio.CancelledError and self._expired:
            self._timeout_handler = None
            raise asyncio.TimeoutError
        # timeout is not expired
        self.reject()
        return None

    def _on_timeout(self, task: 'asyncio.Task[None]') -> None:
        task.cancel()
        self._expired = True


def _current_task(loop: asyncio.AbstractEventLoop) -> 'asyncio.Task[Any]':
    if sys.version_info >= (3, 7):
        return asyncio.current_task(loop=loop)
    else:
        return asyncio.Task.current_task(loop=loop)


def _get_running_loop() -> asyncio.AbstractEventLoop:
    if sys.version_info >= (3, 7):
        return asyncio.get_running_loop()
    else:
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            raise RuntimeError("no running event loop")
        return loop
