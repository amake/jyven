Jyven
=========

A utility for importing Maven dependencies for use with Jython.

Usage
=====

Specify a Maven dependency like this::

    from jyven import maven
    maven('group:artifact:version')

The artifact and its `compile` dependencies will be downloaded from Maven
Central and appended to `sys.path`. To specify a repository other than Maven
Central, use the `repo` kwarg::

    maven('group:artifact:version', repo='http://example.com')

There is also a preset for jCenter::

    from jyven import jcenter
    jcenter('group:artifact:version')

Quick Install
=============

This package is not on PyPI, so install with::

    pip install git+https://github.com/amake/jyven.git

Requirements
============

The Maven 3 executable must be accessible from the path as `mvn`.

Limitations
===========

Maven operations are performed by invoking the Maven executable in a separate
process (and in some cases scraping the output), so it is not very efficient or
robust.

License
=======

Jyven is distributed under the `MIT license <LICENSE.txt>`__.
