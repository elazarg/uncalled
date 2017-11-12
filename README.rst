``uncalled``
============

Find unused functions in Python projects.


This tool uses either regular expressions (the default) or AST traversal.
The regular expressions are *fast* and has surprisingly few false-positives.
To further reduce false positives, there is a combined mode ``both``.


Usage
-----

::

    $ uncalled path/to/project

for more options, see ``uncalled --help``


`vulture <https://pypi.python.org/pypi/vulture>`_ is a similar package.
