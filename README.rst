droprowsbyposition
------------------

Workbench module that drops specified rows.

Developing
----------

First, get up and running:

#. ``python3 ./setup.py test`` # to test Python
#. ``npm install && npm test`` # to test JavaScript

To add a feature on the Python side:

#. Write a test in ``test_droprowsbyposition.py``
#. Run ``python3 ./setup.py test`` to prove it breaks
#. Edit ``droprowsbyposition.py`` to make the test pass
#. Run ``python3 ./setup.py test`` to prove it works
#. Commit and submit a pull request

To add a feature on the JavaScript side:

#. Write a test in ``support.test.js``
#. Run ``npm test`` to prove it breaks
#. Edit ``support.mjs`` to make the test pass
#. Run ``npm test`` to prove it works
#. Commit and submit a pull request

To develop continuously on Workbench:

#. Check out the columnchart repository in a sibling directory to your checked-out Workbench code.
#. Start Workbench with ``CACHE_MODULES=false bin/dev start`` 
#. In a separate tab in the Workbench directory, run ``pipenv run ./manage.py develop-module droprowsbyposition``
#. Edit this code; the module will be reloaded in Workbench immediately. In the Workbench website, modify parameters to execute the reloaded code.

For full instructions, see [developing your own modules](https://github.com/CJWorkbench/cjworkbench/wiki/Creating-A-Module)
