from __future__ import print_function
import re
import sys
import os
from os import path
import subprocess
import logging
from tempfile import TemporaryFile

maven_central_url = 'https://repo1.maven.org/maven2'
jcenter_url = 'https://jcenter.bintray.com'

pom_template = '''<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>id</groupId>
    <artifactId>id</artifactId>
    <version>1.0</version>
    <repositories>
        %(repositories)s
    </repositories>
    <dependencies>
        %(dependencies)s
    </dependencies>
</project>
'''

repo_template = '''<repository>
    <id>%(id)s</id>
    <url>%(url)s</url>
</repository>
'''

mvn_home = path.expanduser('~/.m2')
local_repo = path.join(mvn_home, 'repository')

dep_pattern = re.compile(r'([a-z0-9.:-]+):compile')

user_repos = []

cache_file = None
cache = {}

if sys.argv[0]:
    import json
    cache_dir = path.dirname(path.realpath(sys.argv[0]))
    cache_file = path.join(cache_dir, '.jyven.json')
    logging.debug('Using cache file: %s', cache_file)
    if path.isfile(cache_file):
        with open(cache_file) as infile:
            try:
                cache = json.load(infile)
            except Exception, e:
                logging.error('Failed to load cache: %s', e)


def repositories(repos):
    for repo in repos:
        if repo not in user_repos:
            user_repos.append(repo)


def generate_pom(repos, deps):
    repos_snip = '\n'.join([repo_template % {'id': n, 'url': url}
                            for n, url in enumerate(repos)])
    deps_snip = '\n'.join([dep.to_xml() for dep in deps])
    return pom_template % {'repositories': repos_snip,
                           'dependencies': deps_snip}


class Coordinates(object):
    def __init__(self, coords):
        parts = coords.split(':')
        if len(parts) == 3:
            self.group, self.artifact, self.version = parts
            self.packaging, self.classifier = None, None
        elif len(parts) == 4:
            self.group, self.artifact, self.packaging, self.version = parts
            self.classifier = None
        elif len(parts) == 5:
            self.group, self.artifact, self.packaging, self.classifier, self.version = parts
        else:
            raise Exception
        self.local_path = None
        if path.isdir(local_repo):
            self.local_path = path.join(local_repo,
                                        self.group.replace('.', '/'),
                                        self.artifact, self.version)            

    def to_xml(self):
        parts = ['<dependency>']
        if self.group is not None:
            parts.append('<groupId>%s</groupId>' % self.group)
        if self.artifact is not None:
            parts.append('<artifactId>%s</artifactId>' % self.artifact)
        if self.packaging is not None:
            parts.append('<type>%s</type>' % self.packaging)
        if self.classifier is not None:
            parts.append('<classifier>%s</classifier>' % self.classifier)
        if self.version is not None:
            parts.append('<version>%s</version>' % self.version)
        parts.append('</dependency>')
        return '\n'.join(parts)

    def __repr__(self):
        return ':'.join([part for part in
                         [self.group, self.artifact, self.packaging, self.classifier, self.version]
                         if part is not None])


class Artifact(object):
    def __init__(self, coords, repos=None):
        self.coords = Coordinates(coords)
        self.repos = repos or []

    def _classpath_from_cache(self):
        cached = cache.get(str(self.coords), None)
        if cached and all(path.isfile(item) for item in cached.split(':')):
            return cached
        else:
            return None

    @property
    def classpath(self):
        cached = self._classpath_from_cache()
        if cached:
            return cached
        pom = generate_pom(self.repos, [self.coords])
        logging.debug('Generated POM:\n%s', pom)
        with TemporaryFile() as tmp:
            tmp.write(pom)
            tmp.flush()
            mvn_deplist = ['mvn', 'dependency:build-classpath',
                           '-DincludeScope=compile',
                           '-DpathSeparator=:',
                           '-DoutputAbsoluteArtifactFilename=true',
                           '-Dmdep.outputFilterFile=true',
                           '-f', tmp.name]
            logging.info(' '.join(mvn_deplist))
            cp_output = subprocess.check_output(mvn_deplist)
        cp_def = next(line for line in cp_output.split('\n')
                      if line.startswith('classpath='))
        cp = cp_def[len('classpath='):]
        cache[str(self.coords)] = cp
        return cp

    @property
    def dependency_files(self):
        return self.classpath.split(':')

    def fetch(self):
        mvn_get = ['mvn', 'dependency:get',
                   '-Dartifact=%s' % self.coords]
        if self.repos:
            named = ['%s::::%s' % (n, url) for n, url in enumerate(self.repos)]
            mvn_get.append('-DremoteRepositories=%s' % ','.join(named))
        logging.info(' '.join(mvn_get))
        subprocess.check_call(mvn_get)

    def __nonzero__(self):
        if self._classpath_from_cache():
            return True
        else:
            return (path.isdir(self.coords.local_path) and
                    any(path.splitext(i)[1] == '.pom'
                        for i in os.listdir(self.coords.local_path)))

    def __repr__(self):
        return '<Artifact %s>' % self.coords


def maven(coords, repos=None):
    all_repos = list(user_repos)
    if repos is not None:
        all_repos.extend(repos)
    artifact = Artifact(coords, all_repos)
    if not artifact:
        logging.info('Missing artifact: %s' % artifact)
        artifact.fetch()
    try:
        deps = artifact.dependency_files
    except subprocess.CalledProcessError:
        artifact.fetch()
        deps = artifact.dependency_files
    logging.info('Adding dependency to path: %s', artifact.coords)
    for dep in deps:
        if dep not in sys.path:
            logging.debug(dep)
            sys.path.append(dep)
    if cache_file:
        with open(cache_file, 'w') as outfile:
            logging.debug('Writing cache: entries=%d', len(cache))
            json.dump(cache, outfile)
    return artifact


def jcenter(coords):
    maven(coords, repos=[jcenter_url])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    maven('commons-lang:commons-lang:2.6')
    from org.apache.commons.lang.math import JVMRandom
    print(JVMRandom().nextDouble())
