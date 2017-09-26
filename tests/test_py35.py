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


async def test_async_zero(loop):
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0, loop=loop) as cm:
            await asyncio.sleep(10, loop=loop)
    assert cm.expired


async def test_async_zero_coro_not_started(loop):
    coro_started = False

    async def coro():
        nonlocal coro_started
        coro_started = True

    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0, loop=loop) as cm:
            await asyncio.sleep(0, loop=loop)
            await coro()

    assert cm.expired
    assert coro_started is False
