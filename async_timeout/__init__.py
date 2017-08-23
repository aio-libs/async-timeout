import asyncio


__version__ = '1.3.0'


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
    def __init__(self, timeout, *, loop=None):
        if timeout is not None and timeout == 0:
            timeout = None
        self._timeout = timeout
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._task = None
        self._cancelled = False
        self._cancel_handler = None

    def __enter__(self):
        return self._do_enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._do_exit(exc_type)

    @asyncio.coroutine
    def __aenter__(self):
        return self._do_enter()

    @asyncio.coroutine
    def __aexit__(self, exc_type, exc_val, exc_tb):
        self._do_exit(exc_type)

    @property
    def expired(self):
        return self._cancelled

    def _do_enter(self):
        if self._timeout is not None:
            self._task = current_task(self._loop)
            if self._task is None:
                raise RuntimeError('Timeout context manager should be used '
                                   'inside a task')
            self._cancel_handler = self._loop.call_later(
                self._timeout, self._cancel_task)
        return self

    def _do_exit(self, exc_type):
        if exc_type is asyncio.CancelledError and self._cancelled:
            self._cancel_handler = None
            self._task = None
            raise asyncio.TimeoutError
        if self._timeout is not None and self._cancel_handler is not None:
            self._cancel_handler.cancel()
            self._cancel_handler = None
        self._task = None

    def _cancel_task(self):
        self._task.cancel()
        self._cancelled = True


def current_task(loop):
    task = asyncio.Task.current_task(loop=loop)
    if task is None:
        if hasattr(loop, 'current_task'):
            task = loop.current_task()

    return task
