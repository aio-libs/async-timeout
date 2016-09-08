async_timeout
=============

asyncio-compatible timeout context manage.


Usage example
-------------


Useful in cases when you want to apply timeout logic around block
of code or in cases when asyncio.wait_for is not suitable, e.g::

   >>> with timeout(0.001):
   ...     async with aiohttp.get('https://github.com') as r:
   ...         await r.text()


*timeout* - value in seconds or None to disable timeout logic
*loop* - asyncio compatible event loop


Installation
------------

::

   $ pip install yarl

The library is Python 3 only!



Authors and License
-------------------

The module is written by Andrew Svetlov.

It's *Apache 2* licensed and freely available.
