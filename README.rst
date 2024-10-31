async-timeout
=============
.. image:: https://travis-ci.com/aio-libs/async-timeout.svg?branch=master
    :target: https://travis-ci.com/aio-libs/async-timeout
.. image:: https://codecov.io/gh/aio-libs/async-timeout/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/async-timeout
.. image:: https://img.shields.io/pypi/v/async-timeout.svg
    :target: https://pypi.python.org/pypi/async-timeout
.. image:: https://badges.gitter.im/Join%20Chat.svg
    :target: https://gitter.im/aio-libs/Lobby
    :alt: Chat on Gitter

asyncio-compatible timeout context manager.



DEPRECATED
----------

This library has effectively been upstreamed into Python 3.11+.

Therefore this library is considered deprecated and no longer actively supported.

Version 5.0+ provides dual-mode when executed on Python 3.11+:
``asyncio_timeout.Timeout`` is fully compatible with ``asyncio.Timeout`` *and* old
versions of the library.

Anyway, using upstream is highly recommended. ``asyncio_timeout`` exists only for the
sake of backward compatibility, easy supporting both old and new Python by the same
code, and easy misgration.


Usage example
-------------


The context manager is useful in cases when you want to apply timeout
logic around block of code or in cases when ``asyncio.wait_for()`` is
not suitable. Also it's much faster than ``asyncio.wait_for()``
because ``timeout`` doesn't create a new task.

The ``timeout(delay, *, loop=None)`` call returns a context manager
that cancels a block on *timeout* expiring::

   from async_timeout import timeout
   async with timeout(1.5):
       await inner()

1. If ``inner()`` is executed faster than in ``1.5`` seconds nothing
   happens.
2. Otherwise ``inner()`` is cancelled internally by sending
   ``asyncio.CancelledError`` into but ``asyncio.TimeoutError`` is
   raised outside of context manager scope.

*timeout* parameter could be ``None`` for skipping timeout functionality.


Alternatively, ``timeout_at(when)`` can be used for scheduling
at the absolute time::

   loop = asyncio.get_event_loop()
   now = loop.time()

   async with timeout_at(now + 1.5):
       await inner()


Please note: it is not POSIX time but a time with
undefined starting base, e.g. the time of the system power on.


Context manager has ``.expired()`` / ``.expired`` for check if timeout happens
exactly in context manager::

   async with timeout(1.5) as cm:
       await inner()
   print(cm.expired())  # recommended api
   print(cm.expired)    # compatible api

The property is ``True`` if ``inner()`` execution is cancelled by
timeout context manager.

If ``inner()`` call explicitly raises ``TimeoutError`` ``cm.expired``
is ``False``.

The scheduled deadline time is available as ``.when()`` / ``.deadline``::

   async with timeout(1.5) as cm:
       cm.when()    # recommended api
       cm.deadline  # compatible api

Not finished yet timeout can be rescheduled by ``shift()``
or ``update()`` methods::

   async with timeout(1.5) as cm:
       # recommended api
       cm.reschedule(cm.when() + 1)  # add another second on waiting
       # compatible api
       cm.shift(1)  # add another second on waiting
       cm.update(loop.time() + 5)  # reschedule to now+5 seconds

Rescheduling is forbidden if the timeout is expired or after exit from ``async with``
code block.


Disable scheduled timeout::

   async with timeout(1.5) as cm:
       cm.reschedule(None)  # recommended api
       cm.reject()          # compatible api



Installation
------------

::

   $ pip install async-timeout

The library is Python 3 only!



Authors and License
-------------------

The module is written by Andrew Svetlov.

It's *Apache 2* licensed and freely available.
