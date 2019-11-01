import asyncio
import os
import time

import pytest

from async_timeout import timeout, timeout_at


@pytest.mark.asyncio
async def test_timeout():
    canceled_raised = False

    async def long_running_task():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            nonlocal canceled_raised
            canceled_raised = True
            raise

    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.01) as t:
            await long_running_task()
            assert t._loop is asyncio.get_event_loop()
    assert canceled_raised, 'CancelledError was not raised'


@pytest.mark.asyncio
async def test_timeout_finish_in_time():
    async def long_running_task():
        await asyncio.sleep(0.01)
        return 'done'

    with timeout(0.1):
        resp = await long_running_task()
    assert resp == 'done'


@pytest.mark.asyncio
async def test_timeout_disable():
    async def long_running_task():
        await asyncio.sleep(0.1)
        return 'done'

    loop = asyncio.get_event_loop()
    t0 = loop.time()
    with timeout(None):
        resp = await long_running_task()
    assert resp == 'done'
    dt = loop.time() - t0
    assert 0.09 < dt < 0.13, dt


@pytest.mark.asyncio
async def test_timeout_is_none_no_schedule():
    with timeout(None) as cm:
        assert cm._timeout_handler is None
        assert cm.deadline is None


def test_timeout_no_loop():
    with pytest.raises(RuntimeError,
                       match="no running event loop"):
        timeout(None)


@pytest.mark.asyncio
async def test_timeout_zero():
    with pytest.raises(asyncio.TimeoutError):
        timeout(0)


@pytest.mark.asyncio
async def test_timeout_not_relevant_exception():
    await asyncio.sleep(0)
    with pytest.raises(KeyError):
        with timeout(0.1):
            raise KeyError


@pytest.mark.asyncio
async def test_timeout_canceled_error_is_not_converted_to_timeout():
    await asyncio.sleep(0)
    with pytest.raises(asyncio.CancelledError):
        with timeout(0.001):
            raise asyncio.CancelledError


@pytest.mark.asyncio
async def test_timeout_blocking_loop():
    async def long_running_task():
        time.sleep(0.1)
        return 'done'

    with timeout(0.01):
        result = await long_running_task()
    assert result == 'done'


@pytest.mark.asyncio
async def test_for_race_conditions():
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    loop.call_later(0.1, fut.set_result('done'))
    with timeout(0.2):
        resp = await fut
    assert resp == 'done'


@pytest.mark.asyncio
async def test_timeout_time():
    foo_running = None
    loop = asyncio.get_event_loop()
    start = loop.time()
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.1):
            foo_running = True
            try:
                await asyncio.sleep(0.2)
            finally:
                foo_running = False

    dt = loop.time() - start
    if not (0.09 < dt < 0.11) and os.environ.get('APPVEYOR'):
        pytest.xfail('appveyor sometimes is toooo sloooow')
    assert 0.09 < dt < 0.11
    assert not foo_running


@pytest.mark.asyncio
async def test_outer_coro_is_not_cancelled():

    has_timeout = False

    async def outer():
        nonlocal has_timeout
        try:
            with timeout(0.001):
                await asyncio.sleep(1)
        except asyncio.TimeoutError:
            has_timeout = True

    task = asyncio.ensure_future(outer())
    await task
    assert has_timeout
    assert not task.cancelled()
    assert task.done()


@pytest.mark.asyncio
async def test_cancel_outer_coro():
    loop = asyncio.get_event_loop()
    fut = loop.create_future()

    async def outer():
        fut.set_result(None)
        await asyncio.sleep(1)

    task = asyncio.ensure_future(outer())
    await fut
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    assert task.done()


@pytest.mark.asyncio
async def test_timeout_suppress_exception_chain():
    with pytest.raises(asyncio.TimeoutError) as ctx:
        with timeout(0.01):
            await asyncio.sleep(10)
    assert not ctx.value.__suppress_context__


@pytest.mark.asyncio
async def test_timeout_expired():
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.01) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_timeout_inner_timeout_error():
    with pytest.raises(asyncio.TimeoutError):
        with timeout(0.01) as cm:
            raise asyncio.TimeoutError
    assert not cm.expired


@pytest.mark.asyncio
async def test_timeout_inner_other_error():
    class MyError(RuntimeError):
        pass
    with pytest.raises(MyError):
        with timeout(0.01) as cm:
            raise MyError
    assert not cm.expired


@pytest.mark.asyncio
async def test_timeout_at():
    loop = asyncio.get_event_loop()
    with pytest.raises(asyncio.TimeoutError):
        now = loop.time()
        async with timeout_at(now + 0.01) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_timeout_at_not_fired():
    loop = asyncio.get_event_loop()
    now = loop.time()
    async with timeout_at(now + 1) as cm:
        await asyncio.sleep(0)
    assert not cm.expired


@pytest.mark.asyncio
async def test_expired_after_rejecting():
    t = timeout(10)
    assert not t.expired
    t.reject()
    assert not t.expired


@pytest.mark.asyncio
async def test_expired_after_timeout():
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as t:
            assert not t.expired
            await asyncio.sleep(10)
    assert t.expired


@pytest.mark.asyncio
async def test_deadline():
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(1) as cm:
        t1 = loop.time()
        assert t0 + 1 <= cm.deadline <= t1 + 1


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
async def test_shift_at():
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(1) as cm:
        t1 = loop.time()
        assert t0 + 1 <= cm.deadline <= t1 + 1
        cm.shift_at(t1+1)
        assert t1 + 1 <= cm.deadline <= t1 + 1.001


@pytest.mark.asyncio
async def test_shift():
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(1) as cm:
        t1 = loop.time()
        assert t0 + 1 <= cm.deadline <= t1 + 1
        cm.shift(1)
        assert t1 + 1.999 <= cm.deadline <= t1 + 2.001


@pytest.mark.asyncio
async def test_shift_none_deadline():
    async with timeout(None) as cm:
        with pytest.raises(RuntimeError,
                           match="shifting timeout without deadline"):
            cm.shift(1)


@pytest.mark.asyncio
async def test_shift_negative_expired():
    async with timeout(1) as cm:
        with pytest.raises(asyncio.CancelledError):
            cm.shift(-1)



@pytest.mark.asyncio
async def test_shift_expired():
    async with timeout(0.001) as cm:
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(10)
        with pytest.raises(
            RuntimeError,
            match="cannot reschedule expired timeout"
        ):
            await cm.shift(10)


@pytest.mark.asyncio
async def test_shift_at_expired():
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout_at(t0 + 0.001) as cm:
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(10)
        with pytest.raises(
            RuntimeError,
            match="cannot reschedule expired timeout"
        ):
            await cm.shift_at(t0 + 10)


@pytest.mark.asyncio
async def test_shift_after_cm_exit():
    async with timeout(1) as cm:
        await asyncio.sleep(0)
    with pytest.raises(
        RuntimeError,
        match="cannot reschedule after exit from context manager"
    ):
        cm.shift(1)
