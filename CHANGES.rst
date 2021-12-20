=======
CHANGES
=======

.. towncrier release notes start

4.0.2 (2021-12-20)
==================

Misc
----

- `#259 <https://github.com/aio-libs/async-timeout/issues/259>`_, `#274 <https://github.com/aio-libs/async-timeout/issues/274>`_


4.0.1 (2121-11-10)
==================

- Fix regression:

  1. Don't raise TimeoutError from timeout object that doesn't enter into async context
     manager

  2. Use call_soon() for raising TimeoutError if deadline is reached on entering into
     async context manager

  (#258)

- Make ``Timeout`` class available in ``__all__``.

4.0.0 (2021-11-01)
==================

* Implemented ``timeout_at(deadline)`` (#117)

* Supported ``timeout.deadline`` and ``timeout.expired`` properties.

* Dropped ``timeout.remaining`` property: it can be calculated as
  ``timeout.deadline - loop.time()``

* Dropped ``timeout.timeout`` property that returns a relative timeout based on the
  timeout object creation time; the absolute ``timeout.deadline`` should be used
  instead.

* Added the deadline modification methods: ``timeout.reject()``,
  ``timeout.shift(delay)``, ``timeout.update(deadline)``.

* Deprecated synchronous context manager usage

3.0.1 (2018-10-09)
==================

* More aggressive typing (#48)

3.0.0 (2018-05-05)
==================

* Drop Python 3.4, the minimal supported version is Python 3.5.3

* Provide type annotations

2.0.1 (2018-03-13)
==================

* Fix ``PendingDeprecationWarning`` on Python 3.7 (#33)


2.0.0 (2017-10-09)
==================

* Changed ``timeout <= 0`` behaviour

  * Backward incompatibility change, prior this version ``0`` was
    shortcut for ``None``
  * when timeout <= 0 ``TimeoutError`` raised faster

1.4.0 (2017-09-09)
==================

* Implement ``remaining`` property (#20)

  * If timeout is not started yet or started unconstrained:
    ``remaining`` is ``None``
  * If timeout is expired: ``remaining`` is ``0.0``
  * All others: roughly amount of time before ``TimeoutError`` is triggered

1.3.0 (2017-08-23)
==================

* Don't suppress nested exception on timeout. Exception context points
  on cancelled line with suspended ``await`` (#13)

* Introduce ``.timeout`` property (#16)

* Add methods for using as async context manager (#9)

1.2.1 (2017-05-02)
==================

* Support unpublished event loop's "current_task" api.


1.2.0 (2017-03-11)
==================

* Extra check on context manager exit

* 0 is no-op timeout


1.1.0 (2016-10-20)
==================

* Rename to ``async-timeout``

1.0.0 (2016-09-09)
==================

* The first release.
