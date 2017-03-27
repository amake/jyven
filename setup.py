from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='jyven',
    version='1.0',
    description='Easy inclusion of Maven dependencies for Jython',
    long_description=long_description,
    url='https://github.com/amake/jyven',
    author='Aaron Madlon-Kay',
    author_email='aaron@madlon-kay.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: Jython',
    ],
    keywords='jython maven dependency import',
    py_modules=['jyven'],
)
