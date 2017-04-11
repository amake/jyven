import unittest
import logging
import tempfile
import shutil
import jyven
from jyven import maven, repositories

logging.basicConfig(level=logging.DEBUG)


class TestJyven(unittest.TestCase):
    """Run as e.g. `jython -m unittest jyven_test`."""

    local_repo = None
    
    @classmethod
    def setUpClass(cls):
        TestJyven.local_repo = tempfile.mkdtemp()
        jyven.proj_cache = jyven.Cache(None)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TestJyven.local_repo)
    
    def test_load(self):
        maven('commons-lang:commons-lang:2.6',
              local_repo=self.local_repo)
        from org.apache.commons.lang.math import JVMRandom
        self.assertTrue(isinstance(JVMRandom().nextDouble(), float))

    def test_load_multi(self):
        with repositories(['http://dl.bintray.com/omegat-org/maven',
                           'http://dl.bintray.com/amake/maven'],
                          local_repo=self.local_repo):
            maven('org.omegat:gnudiff4j:1.15')
            maven('org.omegat:juniversalchardet:1.0.4')
            maven('org.madlonkay.supertmxmerge:supertmxmerge:2.0.1')
        from bmsi.util import Diff
        from org.mozilla.universalchardet import UniversalDetector


if __name__ == '__main__':
    unittest.main(verbosity=2)
