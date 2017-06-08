import codecs
import os
import re
from setuptools import setup, find_packages


PACKAGE_NAME = 'pong'
PACKAGE_DIR = os.path.dirname(__file__)
SCRIPT_DIR = os.path.join(PACKAGE_DIR, 'bin')


def read(fname):
    with codecs.open(fname, 'r', encoding='utf-8') as f:
        return f.read()


def get_version(package):
    init_py_path = os.path.join(package, '__init__.py')
    init_py = read(init_py_path)
    # if version isn't set, this will error out
    # #featurenotabug
    version = re.search('''__version__ = ['"]([^'"]+)['"]''', init_py).group(1)
    return version


def get_script_path(name):
    return os.path.join(SCRIPT_DIR, name)


setup(
    name='pong',
    version=get_version(PACKAGE_NAME),
    author='Chuck Bassett',
    author_email='iamchuckb@gmail.com',
    description='Program like it is 1972',
    license='MIT',
    url='https://github.com/chucksmash/pong.git',
    keywordsd='pong pygame games',
    packages=find_packages(exclude=['tests']),
    long_description=read('README.md'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=[],
    scripts=[
        get_script_path('pong'),
    ],
    package_data={
        '': ['README.md'],
    },
    zip_safe=False
)
