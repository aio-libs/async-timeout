import asyncio

import pytest

from async_timeout import timeout


async def test_async_timeout(loop):
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01, loop=loop) as cm:
            await asyncio.sleep(10, loop=loop)
    assert cm.expired


async def test_async_no_timeout(loop):
    async with timeout(1, loop=loop) as cm:
        await asyncio.sleep(0, loop=loop)
    assert not cm.expired
