Functional / regression test suite for `amo-validator`_, the Add-on validator
used at http://addons.mozilla.org/

Install
=======

You need Python 2.6 or higher.  Then clone this repo::

  git clone git://github.com/mozilla/test-amo-validator.git

Install the dependencies::

  cd test-amo-validator
  pip install -r requirements.txt

You'll probably want to do all of this inside a virtualenv_ using
`virtualenvwrapper`_.

Usage
=====

::

  cd test-amo-validator
  nosetests

Then make a cup of tea while all of those tests run.  It takes a while.

.. _`amo-validator`: https://github.com/mozilla/amo-validator
.. _`virtualenv`: http://pypi.python.org/pypi/virtualenv
.. _`virtualenvwrapper`: http://www.doughellmann.com/docs/virtualenvwrapper/