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

proj_root = (path.dirname(path.realpath(sys.argv[0]))
             if sys.argv[0] else None)
proj_cache_file = path.join(proj_root, '.jyven.json') if proj_root else None

dep_pattern = re.compile(r'([a-z0-9.:-]+):compile')

user_repos = []


def env_to_args(env):
    return ['-D%s=%s' % pair for pair in env.iteritems()]


class Maven(object):
    def __init__(self, repos, cache, local_repo=None):
        self.repos = repos if repos else []
        self.cache = cache
        self.local_repo = local_repo

    def _invoke(self, args, env):
        raise NotImplemented

    def _invoke_get_output(self, args, env):
        raise NotImplemented

    def dependency_build_classpath(self, pom):
        args = ['dependency:build-classpath',
                       '-f', pom]
        env = {'includeScope': 'compile',
               'pathSeparator': ':',
               'outputAbsoluteArtifactFilename': 'true',
               'mdep.outputFilterFile': 'true'}
        if self.local_repo:
            env['maven.repo.local'] = self.local_repo
        logging.info(' '.join(args + env_to_args(env)))
        output = self._invoke_get_output(args, env)
        cp_def = next(line for line in output.split('\n')
                      if line.startswith('classpath='))
        return cp_def[len('classpath='):]

    def dependency_get(self, coords):
        args = ['dependency:get']
        env = {'artifact': '%s' % coords}
        if self.repos:
            named = ['%s::::%s' % (n, url)
                     for n, url in enumerate(self.repos)]
            env['remoteRepositories'] = ','.join(named)
        if self.local_repo:
            env['maven.repo.local'] = self.local_repo
        logging.info(' '.join(args + env_to_args(env)))
        self._invoke(args, env)

    def dependency_files(self, coords):
        return self.get_classpath(coords).split(':')

    def get_classpath(self, coords):
        classpath = self.cache.fetch(coords)
        if not classpath:
            classpath = self._get_classpath_impl(coords)
            self.cache.store(coords, classpath)
        return classpath

    def _get_classpath_impl(self, coords):
        pom = generate_pom(self.repos, [Coordinates(coords)])
        logging.debug('Generated POM:\n%s', pom)
        with TemporaryFile() as tmp:
            tmp.write(pom)
            tmp.flush()
            try:
                return self.dependency_build_classpath(tmp.name)
            except subprocess.CalledProcessError:
                self.dependency_get(coords)
                return self.dependency_build_classpath(tmp.name)


class MavenCli(Maven):
    def _cmd(self, args, env):
        return ['mvn'] + args + env_to_args(env)
        
    def _invoke(self, args, env):
        subprocess.check_call(self._cmd(args, env))

    def _invoke_get_output(self, args, env):
        return subprocess.check_output(self._cmd(args, env))


class Cache(object):
    def __init__(self, cache_file):
        self.cache = {}
        self.json = None
        self.cache_file = cache_file
        if cache_file:
            import json
            self.json = json
            if path.isfile(cache_file):
                self._load(cache_file)

    def _load(self, cache_file):
        logging.debug('Loading cache file: %s', cache_file)
        with open(cache_file) as infile:
            try:
                self.cache.update(self.json.load(infile))
            except Exception, e:
                logging.error('Failed to load cache: %s', e)

    def fetch(self, coords):
        cached = self.cache.get(str(coords), None)
        return cached if self.check_classpath(cached) else None

    def check_classpath(self, classpath):
        return classpath and all(path.isfile(item)
                                 for item in classpath.split(':'))

    def store(self, coords, classpath):
        self.cache[str(coords)] = classpath
        if self.cache_file and self.json:
            with open(self.cache_file, 'w') as outfile:
                logging.debug('Writing cache: entries=%d', len(self.cache))
                self.json.dump(self.cache, outfile)


cache = Cache(proj_cache_file)


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


def maven(coords, repos=None):
    all_repos = list(user_repos)
    if repos is not None:
        all_repos.extend(repos)
    mvn = MavenCli(all_repos, cache)
    deps = mvn.dependency_files(coords)
    logging.debug('Adding dependency to path: %s', coords)
    add_to_path(deps)


def add_to_path(deps):
    for dep in deps:
        if dep not in sys.path:
            logging.debug(dep)
            sys.path.append(dep)


def jcenter(coords):
    return maven(coords, repos=[jcenter_url])


if __name__ == '__main__':
    pass
