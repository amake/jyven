Jyven
=========

A utility for importing Maven dependencies for use with Jython.

Usage
=====

Specify a Maven dependency like this::

    from jyven import maven
    maven('group:artifact:version')

The artifact and its `compile` dependencies will be downloaded with Maven and
appended to `sys.path`.

Quick Install
=============

This package is not on PyPI, so install with::

    pip install git+https://github.com/amake/jyven.git

Requirements
============

The Maven executable must be accessible from the path as `mvn`.

Limitations
===========

Maven operations are performed by invoking the Maven executable in a separate
process (and in some cases scraping the output), so it is not very efficient or
robust.

License
=======

Jyven is distributed under the `MIT license <LICENSE.txt>`__.
