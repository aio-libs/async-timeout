import asyncio

import pytest

from async_timeout import timeout


@pytest.mark.asyncio
async def test_async_timeout():
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_async_no_timeout():
    async with timeout(1) as cm:
        await asyncio.sleep(0)
    assert not cm.expired


@pytest.mark.asyncio
async def test_async_zero():
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_async_zero_coro_not_started():
    coro_started = False

    async def coro():
        nonlocal coro_started
        coro_started = True

    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0) as cm:
            await asyncio.sleep(0)
            await coro()

    assert cm.expired
    assert coro_started is False
