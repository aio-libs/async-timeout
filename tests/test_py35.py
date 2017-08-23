import asyncio

import pytest

from async_timeout import timeout


async def test_async_timeout(loop):
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01, loop=loop):
            yield from asyncio.sleep(10, loop=loop)


async def test_async_no_timeout(loop):
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(1, loop=loop):
            yield from asyncio.sleep(0, loop=loop)
