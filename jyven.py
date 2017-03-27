from __future__ import print_function
import re
import sys
import os
from os import path
import subprocess
import logging

mvn_home = path.expanduser('~/.m2')

dep_pattern = re.compile(r'([a-z0-9.:-]+):compile')


class Artifact(object):
    def __init__(self, artifact_id):
        self.id = artifact_id
        home = artifact_to_path(artifact_id)
        for f in os.listdir(home):
            _, ext = path.splitext(f)
            setattr(self, ext[1:], path.join(home, f))

    @property
    def dependencies(self):
        mvn_deplist = ['mvn', 'dependency:list',
                       '-DincludeScope=compile',
                       '-f', self.pom]
        deps_text = subprocess.check_output(mvn_deplist)
        return dep_pattern.findall(deps_text)

    @property
    def dependency_files(self):
        return [artifact_to_path(d) for d in self.dependencies]

    def __nonzero__(self):
        return len(vars(self)) > 1

    def __repr__(self):
        return '<Artifact %s>' % self.id


def artifact_to_path(artifact_id):
    parts = artifact_id.split(':')
    if len(parts) == 3:
        grp, art, ver = parts
        typ = None
    elif len(parts) == 4:
        grp, art, typ, ver = parts
    home = path.join(mvn_home, 'repository',
                     grp.replace('.', '/'), art, ver)
    return (home if typ is None
            else path.join(home, '%s-%s.%s' % (art, ver, typ)))


def maven(artifact_id, repo=None):
    artifact = Artifact(artifact_id)
    if not artifact:
        logging.info('Missing artifact: %s' % artifact)
        mvn_get = ['mvn', 'dependency:get',
                   '-Dartifact=%s' % artifact.id]
        if repo is not None:
            mvn_get.append('-DrepoUrl=%s' % repo)
        subprocess.check_call(mvn_get)
    deps = artifact.dependency_files
    logging.info('Adding dependency to path: %s', artifact.id)
    sys.path.append(artifact.jar)
    logging.info('Adding recursive dependencies to path: %s', deps)
    sys.path.extend(deps)


if __name__ == '__main__':
    maven('commons-lang:commons-lang:2.6')
    from org.apache.commons.lang.math import JVMRandom
    print(JVMRandom().nextDouble())
