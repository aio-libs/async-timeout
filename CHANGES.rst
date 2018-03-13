CHANGES
=======

2.0.1 (2018-03-13)
------------------

* Fix ``PendingDeprecationWarning`` on Python 3.7 (#33)


2.0.0 (2017-10-09)
------------------

* Changed `timeout <= 0` behaviour

  * Backward incompatibility change, prior this version `0` was
    shortcut for `None`
  * when timeout <= 0 `TimeoutError` raised faster

1.4.0 (2017-09-09)
------------------

* Implement `remaining` property (#20)

  * If timeout is not started yet or started unconstrained:
    `remaining` is `None`
  * If timeout is expired: `remaining` is `0.0`
  * All others: roughly amount of time before `TimeoutError` is triggered

1.3.0 (2017-08-23)
------------------

* Don't suppress nested exception on timeout. Exception context points
  on cancelled line with suspended `await` (#13)

* Introduce `.timeout` property (#16)

* Add methods for using as async context manager (#9)

1.2.1 (2017-05-02)
------------------

* Support unpublished event loop's "current_task" api.


1.2.0 (2017-03-11)
------------------

* Extra check on context manager exit

* 0 is no-op timeout


1.1.0 (2016-10-20)
------------------

* Rename to `async-timeout`

1.0.0 (2016-09-09)
------------------

* The first release.
