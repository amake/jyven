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
    def __init__(self, coords):
        self.coords = coords
        self._load_artifacts()

    def _load_artifacts(self):
        home = coords_to_path(self.coords)
        if path.isdir(home):
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
        return [coords_to_path(d) for d in self.dependencies]

    def fetch(self, repo=None):
        mvn_get = ['mvn', 'dependency:get',
                   '-Dartifact=%s' % self.coords]
        if repo is not None:
            mvn_get.append('-DremoteRepositories=%s' % repo)
        subprocess.check_call(mvn_get)
        self._load_artifacts()

    def __nonzero__(self):
        return hasattr(self, 'pom')

    def __repr__(self):
        return '<Artifact %s>' % self.coords


def coords_to_path(coords):
    parts = coords.split(':')
    if len(parts) == 3:
        group_id, artifact_id, version = parts
        packaging, classifier = None, None
    elif len(parts) == 4:
        group_id, artifact_id, packaging, version = parts
        classifier = None
    elif len(parts) == 5:
        group_id, artifact_id, packaging, classifier, version = parts
    else:
        raise Exception
    home = path.join(mvn_home, 'repository',
                     group_id.replace('.', '/'), artifact_id, version)
    return (home if packaging is None
            else path.join(home, '%s-%s.%s' % (artifact_id, version, packaging)))


def maven(coords, repo=None):
    artifact = Artifact(coords)
    if not artifact:
        logging.info('Missing artifact: %s' % artifact)
        artifact.fetch(repo=repo)
    deps = [artifact.jar] + artifact.dependency_files
    for dep in deps:
        if dep not in sys.path:
            logging.info('Adding dependency to path: %s', artifact.coords)
            sys.path.append(dep)


def jcenter(coords):
    maven(coords, repo='https://jcenter.bintray.com/')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    maven('commons-lang:commons-lang:2.6')
    from org.apache.commons.lang.math import JVMRandom
    print(JVMRandom().nextDouble())
