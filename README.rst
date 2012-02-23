===========
microsearch
===========


A small search library.

Primarily intended to be a learning tool to teach the fundamentals of search.

Useful for embedding into Python apps where you don't want/need something
as complex as Lucene.

Part of my (upcoming) 2012 PyCon talk - https://us.pycon.org/2012/schedule/presentation/66/


Requirements
============

* Python 2.5+ or Python 3.2+
* (Optional) simplejson
* (Optional) unittest2 (Python 2.5 - for runnning the tests)


Usage
=====

Example::

    import microsearch

    # Create an instance, pointing it to where the data should be stored.
    ms = microsearch.Microsearch('/tmp/microsearch')

    # Index some data.
    ms.index('email_1', {'text': "Peter,\n\nI'm going to need those TPS reports on my desk first thing tomorrow! And clean up your desk!\n\nLumbergh"})
    ms.index('email_2', {'text': 'Everyone,\n\nM-m-m-m-my red stapler has gone missing. H-h-has a-an-anyone seen it?\n\nMilton'})
    ms.index('email_3', {'text': "Peter,\n\nYeah, I'm going to need you to come in on Saturday. Don't forget those reports.\n\nLumbergh"})
    ms.index('email_4', {'text': 'How do you feel about becoming Management?\n\nThe Bobs'})

    # Search on it.
    ms.search('Peter')
    ms.search('tps report')


Shortcomings
============

This library is meant to help others learn. While it has full test coverage,
it may not be suitable for production use. Reasons you may not want to use it
in Real Code(tm):

* No concurrency support

  * Tries to work atomically with files
  * But there are no locks
  * So it's possible for writes to overlap between processes

* Maybe thread-safe?

  * Pretty much everything is on an instance
  * But I haven't tested it extensively with threading

* No support for deleting documents

  * If an existing document changes or gets deleted, stale data will be left
    in the index
  * A workaround would be blowing away the index directory, moving the docs out
    and reindexing them :/

* Only n-grams are supported

  * Because writing a full Porter or Snowball stemmer is beyond the needs
    of this library

* No clue on performance at scale

  * This is a proof-of-concept & learning tool, *not* Lucene!
  * With a 2011 MBP on the first 1.2K docs of the Enron corpus:

    * Indexing is pretty slow at ~1 document per second
    * Search is pretty fast at ~0.007 sec per query
    * RAM never exceeded 15Mb when indexing, 10Mb when searching
    * Script in the source repo as ``enron_bench.py``.


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
:date: 2011/02/22
