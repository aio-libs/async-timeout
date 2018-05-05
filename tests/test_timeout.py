import asyncio
import os
import time

import pytest

from async_timeout import timeout

try:
    from asyncio import ensure_future
except ImportError:
    ensure_future = asyncio.async


pytestmark = pytest.mark.asyncio


def create_future(loop):
    """Compatibility wrapper for the loop.create_future() call introduced in
    3.5.2."""
    if hasattr(loop, 'create_future'):
        return loop.create_future()
    else:
        return asyncio.Future(loop=loop)


async def test_timeout(loop):
    canceled_raised = False

    async def long_running_task():
        try:
            await asyncio.sleep(10, loop=loop)
        except asyncio.CancelledError:
            nonlocal canceled_raised
            canceled_raised = True
            raise

    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.01, loop=loop) as t:
            await long_running_task()
            assert t._loop is loop
    assert canceled_raised, 'CancelledError was not raised'


async def test_timeout_finish_in_time(loop):
    async def long_running_task():
        await asyncio.sleep(0.01, loop=loop)
        return 'done'

    with timeout(0.1, loop=loop):
        resp = await long_running_task()
    assert resp == 'done'


def test_timeout_global_loop(loop):
    asyncio.set_event_loop(loop)

    async def run():
        with timeout(10) as t:
            await asyncio.sleep(0.01)
            assert t._loop is loop

    loop.run_until_complete(run())


async def test_timeout_disable(loop):
    async def long_running_task():
        await asyncio.sleep(0.1, loop=loop)
        return 'done'

    t0 = loop.time()
    with timeout(None, loop=loop):
        resp = await long_running_task()
    assert resp == 'done'
    dt = loop.time() - t0
    assert 0.09 < dt < 0.13, dt


def test_timeout_is_none_no_task(loop):
    with timeout(None, loop=loop) as cm:
        assert cm._task is None


async def test_timeout_enable_zero(loop):
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0, loop=loop) as cm:
            await asyncio.sleep(0.1, loop=loop)

    assert cm.expired


async def test_timeout_enable_zero_coro_not_started(loop):
    coro_started = False

    async def coro():
        nonlocal coro_started
        coro_started = True

    with pytest.raises(asyncio.TimeoutError):
        with timeout(0, loop=loop) as cm:
            await asyncio.sleep(0, loop=loop)
            await coro()

    assert cm.expired
    assert coro_started is False


async def test_timeout_not_relevant_exception(loop):
    await asyncio.sleep(0, loop=loop)
    with pytest.raises(KeyError):
        with timeout(0.1, loop=loop):
            raise KeyError


async def test_timeout_canceled_error_is_not_converted_to_timeout(loop):
    await asyncio.sleep(0, loop=loop)
    with pytest.raises(asyncio.CancelledError):
        with timeout(0.001, loop=loop):
            raise asyncio.CancelledError


async def test_timeout_blocking_loop(loop):
    async def long_running_task():
        time.sleep(0.1)
        return 'done'

    with timeout(0.01, loop=loop):
        result = await long_running_task()
    assert result == 'done'


async def test_for_race_conditions(loop):
    fut = create_future(loop)
    loop.call_later(0.1, fut.set_result('done'))
    with timeout(0.2, loop=loop):
        resp = await fut
    assert resp == 'done'


async def test_timeout_time(loop):
    foo_running = None

    start = loop.time()
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.1, loop=loop):
            foo_running = True
            try:
                await asyncio.sleep(0.2, loop=loop)
            finally:
                foo_running = False

    dt = loop.time() - start
    if not (0.09 < dt < 0.11) and os.environ.get('APPVEYOR'):
        pytest.xfail('appveyor sometimes is toooo sloooow')
    assert 0.09 < dt < 0.11
    assert not foo_running


def test_raise_runtimeerror_if_no_task(loop):
    with pytest.raises(RuntimeError):
        with timeout(0.1, loop=loop):
            pass


async def test_outer_coro_is_not_cancelled(loop):

    has_timeout = False

    async def outer():
        nonlocal has_timeout
        try:
            with timeout(0.001, loop=loop):
                await asyncio.sleep(1, loop=loop)
        except asyncio.TimeoutError:
            has_timeout = True

    task = ensure_future(outer(), loop=loop)
    await task
    assert has_timeout
    assert not task.cancelled()
    assert task.done()


async def test_cancel_outer_coro(loop):
    fut = create_future(loop)

    async def outer():
        fut.set_result(None)
        await asyncio.sleep(1, loop=loop)

    task = ensure_future(outer(), loop=loop)
    await fut
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    assert task.done()


async def test_timeout_suppress_exception_chain(loop):
    with pytest.raises(asyncio.TimeoutError) as ctx:
        with timeout(0.01, loop=loop):
            await asyncio.sleep(10, loop=loop)
    assert not ctx.value.__suppress_context__


async def test_timeout_expired(loop):
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.01, loop=loop) as cm:
            await asyncio.sleep(10, loop=loop)
    assert cm.expired


async def test_timeout_inner_timeout_error(loop):
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.01, loop=loop) as cm:
            raise asyncio.TimeoutError
    assert not cm.expired


async def test_timeout_inner_other_error(loop):
    with pytest.raises(RuntimeError):
        with timeout(0.01, loop=loop) as cm:
            raise RuntimeError
    assert not cm.expired


async def test_timeout_remaining(loop):
    with timeout(None, loop=loop) as cm:
        assert cm.remaining is None

    t = timeout(1.0, loop=loop)
    assert t.remaining is None

    with timeout(1.0, loop=loop) as cm:
        await asyncio.sleep(0.1, loop=loop)
        assert cm.remaining < 1.0

    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.1, loop=loop) as cm:
            await asyncio.sleep(0.5, loop=loop)

    assert cm.remaining == 0.0
