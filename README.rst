async_timeout
=============

asyncio-compatible timeout context manager.


Usage example
-------------


The context manager is useful in cases when you want to apply timeout
logic around block of code or in cases when ``asyncio.wait_for()`` is
not suitable. Also it's much faster than ``asyncio.wait_for()``
because ``timeout`` doesn't create a new task.

The ``timeout(timeout, *, loop=None)`` call returns a context manager
that cancels a block on *timeout* expiring::

       with timeout(1.5):
           yield from inner()

   1. If ``inner()`` is executed faster than in ``1.5`` seconds
      nothing happens.
   2. Otherwise ``inner()`` is cancelled internally by sending
      ``asyncio.CancelledError`` into but ``asyncio.TimeoutError``
      is raised outside of context manager scope.


Installation
------------

::

   $ pip install yarl

The library is Python 3 only!



Authors and License
-------------------

The module is written by Andrew Svetlov.

It's *Apache 2* licensed and freely available.
