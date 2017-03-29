import unittest
import logging
from jyven import maven


class TestJyven(unittest.TestCase):
    """Run as e.g. `jython -m unittest jyven_test`."""

    def test_load(self):
        logging.basicConfig(level=logging.DEBUG)
        maven('commons-lang:commons-lang:2.6')
        from org.apache.commons.lang.math import JVMRandom
        self.assertTrue(isinstance(JVMRandom().nextDouble(), float))
