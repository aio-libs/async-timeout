CHANGES
=======

1.3.0 (2017-xx-xx)
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
