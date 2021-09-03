import asyncio
import sys
import time

import pytest

from async_timeout import Timeout, timeout, timeout_at


@pytest.mark.asyncio
async def test_timeout() -> None:
    canceled_raised = False

    async def long_running_task() -> None:
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            nonlocal canceled_raised
            canceled_raised = True
            raise

    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as t:
            await long_running_task()
            assert t._loop is asyncio.get_event_loop()
    assert canceled_raised, "CancelledError was not raised"


@pytest.mark.asyncio
async def test_timeout_finish_in_time() -> None:
    async def long_running_task() -> str:
        await asyncio.sleep(0.01)
        return "done"

    async with timeout(0.1):
        resp = await long_running_task()
    assert resp == "done"


@pytest.mark.asyncio
async def test_timeout_disable() -> None:
    async def long_running_task() -> str:
        await asyncio.sleep(0.1)
        return "done"

    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(None):
        resp = await long_running_task()
    assert resp == "done"
    dt = loop.time() - t0
    assert 0.09 < dt < 0.3, dt


@pytest.mark.asyncio
async def test_timeout_is_none_no_schedule() -> None:
    async with timeout(None) as cm:
        assert cm._timeout_handler is None
        assert cm.deadline is None


def test_timeout_no_loop() -> None:
    with pytest.raises(RuntimeError, match="no running event loop"):
        timeout(None)


@pytest.mark.asyncio
async def test_timeout_zero() -> None:
    with pytest.raises(asyncio.TimeoutError):
        timeout(0)


@pytest.mark.asyncio
async def test_timeout_not_relevant_exception() -> None:
    await asyncio.sleep(0)
    with pytest.raises(KeyError):
        async with timeout(0.1):
            raise KeyError


@pytest.mark.asyncio
async def test_timeout_canceled_error_is_not_converted_to_timeout() -> None:
    await asyncio.sleep(0)
    with pytest.raises(asyncio.CancelledError):
        async with timeout(0.001):
            raise asyncio.CancelledError


@pytest.mark.asyncio
async def test_timeout_blocking_loop() -> None:
    async def long_running_task() -> str:
        time.sleep(0.1)
        return "done"

    async with timeout(0.01):
        result = await long_running_task()
    assert result == "done"


@pytest.mark.asyncio
async def test_for_race_conditions() -> None:
    loop = asyncio.get_event_loop()
    fut = loop.create_future()
    loop.call_later(0.1, fut.set_result, "done")
    async with timeout(0.5):
        resp = await fut
    assert resp == "done"


@pytest.mark.asyncio
async def test_timeout_time() -> None:
    foo_running = None
    loop = asyncio.get_event_loop()
    start = loop.time()
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.1):
            foo_running = True
            try:
                await asyncio.sleep(0.2)
            finally:
                foo_running = False

    dt = loop.time() - start
    assert 0.09 < dt < 0.3
    assert not foo_running


@pytest.mark.asyncio
async def test_outer_coro_is_not_cancelled() -> None:

    has_timeout = False

    async def outer() -> None:
        nonlocal has_timeout
        try:
            async with timeout(0.001):
                await asyncio.sleep(1)
        except asyncio.TimeoutError:
            has_timeout = True

    task = asyncio.ensure_future(outer())
    await task
    assert has_timeout
    assert not task.cancelled()
    assert task.done()


@pytest.mark.asyncio
async def test_cancel_outer_coro() -> None:
    loop = asyncio.get_event_loop()
    fut = loop.create_future()

    async def outer() -> None:
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
async def test_timeout_suppress_exception_chain() -> None:
    with pytest.raises(asyncio.TimeoutError) as ctx:
        async with timeout(0.01):
            await asyncio.sleep(10)
    assert not ctx.value.__suppress_context__


@pytest.mark.asyncio
async def test_timeout_expired() -> None:
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_timeout_inner_timeout_error() -> None:
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as cm:
            raise asyncio.TimeoutError
    assert not cm.expired


@pytest.mark.asyncio
async def test_timeout_inner_other_error() -> None:
    class MyError(RuntimeError):
        pass

    with pytest.raises(MyError):
        async with timeout(0.01) as cm:
            raise MyError
    assert not cm.expired


@pytest.mark.asyncio
async def test_timeout_at() -> None:
    loop = asyncio.get_event_loop()
    with pytest.raises(asyncio.TimeoutError):
        now = loop.time()
        async with timeout_at(now + 0.01) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_timeout_at_not_fired() -> None:
    loop = asyncio.get_event_loop()
    now = loop.time()
    async with timeout_at(now + 1) as cm:
        await asyncio.sleep(0)
    assert not cm.expired


@pytest.mark.asyncio
async def test_expired_after_rejecting() -> None:
    t = timeout(10)
    assert not t.expired
    t.reject()
    assert not t.expired


@pytest.mark.asyncio
async def test_reject_finished() -> None:
    async with timeout(10) as t:
        await asyncio.sleep(0)

    assert not t.expired
    with pytest.raises(RuntimeError, match="invalid state EXIT"):
        t.reject()


@pytest.mark.asyncio
async def test_expired_after_timeout() -> None:
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as t:
            assert not t.expired
            await asyncio.sleep(10)
    assert t.expired


@pytest.mark.asyncio
async def test_deadline() -> None:
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(1) as cm:
        t1 = loop.time()
        assert cm.deadline is not None
        assert t0 + 1 <= cm.deadline <= t1 + 1


@pytest.mark.asyncio
async def test_async_timeout() -> None:
    with pytest.raises(asyncio.TimeoutError):
        async with timeout(0.01) as cm:
            await asyncio.sleep(10)
    assert cm.expired


@pytest.mark.asyncio
async def test_async_no_timeout() -> None:
    async with timeout(1) as cm:
        await asyncio.sleep(0)
    assert not cm.expired


@pytest.mark.asyncio
async def test_shift_to() -> None:
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(1) as cm:
        t1 = loop.time()
        assert cm.deadline is not None
        assert t0 + 1 <= cm.deadline <= t1 + 1
        cm.shift_to(t1 + 1)
        assert t1 + 1 <= cm.deadline <= t1 + 1.1


@pytest.mark.asyncio
async def test_shift_by() -> None:
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout(1) as cm:
        t1 = loop.time()
        assert cm.deadline is not None
        assert t0 + 1 <= cm.deadline <= t1 + 1
        cm.shift_by(1)
        assert t1 + 0.999 <= cm.deadline <= t1 + 1.1


@pytest.mark.asyncio
async def test_shift_by_negative_expired() -> None:
    async with timeout(1) as cm:
        with pytest.raises(asyncio.CancelledError):
            cm.shift_by(-1)


@pytest.mark.asyncio
async def test_shift_by_expired() -> None:
    async with timeout(0.001) as cm:
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(10)
        with pytest.raises(RuntimeError, match="cannot reschedule expired timeout"):
            cm.shift_by(10)


@pytest.mark.asyncio
async def test_shift_to_expired() -> None:
    loop = asyncio.get_event_loop()
    t0 = loop.time()
    async with timeout_at(t0 + 0.001) as cm:
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(10)
        with pytest.raises(RuntimeError, match="cannot reschedule expired timeout"):
            cm.shift_to(t0 + 10)


@pytest.mark.asyncio
async def test_shift_by_after_cm_exit() -> None:
    async with timeout(1) as cm:
        await asyncio.sleep(0)
    with pytest.raises(
        RuntimeError, match="cannot reschedule after exit from context manager"
    ):
        cm.shift_by(1)


@pytest.mark.asyncio
async def test_enter_twice() -> None:
    async with timeout(10) as t:
        await asyncio.sleep(0)

    with pytest.raises(RuntimeError, match="invalid state EXIT"):
        async with t:
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_deprecated_with() -> None:
    with pytest.warns(DeprecationWarning):
        with timeout(1):
            await asyncio.sleep(0)


@pytest.mark.skipif(sys.version_info < (3, 7), reason="Not supported in 3.6")
@pytest.mark.asyncio
async def test_race_condition_cancel_before() -> None:
    """Test race condition when cancelling before timeout.

    If cancel happens immediately before the timeout, then
    the timeout may overrule the cancellation, making it
    impossible to cancel some tasks.
    """

    async def test_task(deadline: float, loop: asyncio.AbstractEventLoop) -> None:
        # We need the internal Timeout class to specify the deadline (not delay).
        # This is needed to create the precise timing to reproduce the race condition.
        with pytest.warns(DeprecationWarning):
            with Timeout(deadline, loop):
                await asyncio.sleep(10)

    loop = asyncio.get_running_loop()
    deadline = loop.time() + 1
    t = asyncio.create_task(test_task(deadline, loop))
    loop.call_at(deadline, t.cancel)
    # If we get a TimeoutError, then the code is broken.
    with pytest.raises(asyncio.CancelledError):
        await t

@pytest.mark.xfail(reason="Can't see a way to fix this currently.")
@pytest.mark.skipif(sys.version_info < (3, 9), reason="Can't be fixed in <3.9.")
@pytest.mark.asyncio
async def test_race_condition_cancel_after() -> None:
    """Test race condition when cancelling after timeout.

    Similarly to the previous test, if a cancel happens
    immediately after the timeout (but before the __exit__),
    then the explicit cancel can get overruled again.
    """

    async def test_task(deadline: float, loop: asyncio.AbstractEventLoop) -> None:
        # We need the internal Timeout class to specify the deadline (not delay).
        # This is needed to create the precise timing to reproduce the race condition.
        with pytest.warns(DeprecationWarning):
            with Timeout(deadline, loop):
                await asyncio.sleep(10)

    loop = asyncio.get_running_loop()
    deadline = loop.time() + 1
    t = asyncio.create_task(test_task(deadline, loop))
    loop.call_at(deadline + 0.000001, t.cancel)
    # If we get a TimeoutError, then the code is broken.
    with pytest.raises(asyncio.CancelledError):
        await t
