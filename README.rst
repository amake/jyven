Jyven
=========

A utility for importing Maven dependencies for use with Jython.

Usage
=====

Specify a Maven dependency like this::

    from jyven import maven
    maven('group:artifact:version')

The artifact and its ``compile`` dependencies will be downloaded from Maven
Central and appended to ``sys.path``. To specify repositories other than Maven
Central, use the ``repos`` kwarg::

    maven('group:artifact:version', repos=['http://example.com'])

There is also a preset for JCenter::

    from jyven import jcenter
    jcenter('group:artifact:version')

Use the ``repositories`` context manager to specify repositories for a group of
dependencies and resolve them all at once (this is more efficient than adding
them one at a time)::

    from jyven import maven, repositories
    with repositories(['http://example.com', 'http://localnexus']):
        maven('group:artifact:version')
        maven('group2:artifact2:version2')

Quick Install
=============

This package is not on PyPI, so install with::

    pip install git+https://github.com/amake/jyven.git

Requirements
============

The Maven 3 executable must be accessible from the path as ``mvn``.

Limitations
===========

Maven operations are performed by invoking the Maven executable in a separate
process (and in some cases scraping the output), so it is not very efficient or
robust.

Notes
=====

Because invoking ``mvn`` is slow, Jyven caches resolved classpaths in a
``.jyven.json`` file alongside the invoked script. This should be excluded from
VCS. When invoked in a REPL, no caching is performed.

License
=======

Jyven is distributed under the `MIT license <LICENSE.txt>`__.
