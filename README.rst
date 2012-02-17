===========
microsearch
===========


A small search library.

Primarily intended to be a learning tool to teach the fundamentals of search.

Useful for embedding into Python apps where you don't want/need something
as complex as Lucene.


Requirements
============

* Python 2.5+ or Python 3.2+
* (Optional) simplejson
* (Optional) unittest2 (Python 2.5 - for runnning the tests)


Running Tests
=============

With a source checkout, run:

In Python 2:

    python -m unittest2 tests

In Python 3:

    python -m unittest tests

Tests should be passing at all times under both Python 2.7 & Python 3.2.


Contributions
=============

If you wish to contribute to improving ``microsearch``, the code you submit
must:

* Be your own work & BSD-licensed
* Include a working fix/feature
* Follow the existing style of the codebase
* Include passing test coverage of the new code
* If it's user-facing, must include documentation

Other submissions are welcome, but won't get merged until all of these
requirements are met.


:author: Daniel Lindsley <daniel@toastdriven.com>
:date: 2011/02/16
