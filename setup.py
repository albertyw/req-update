#!/usr/bin/env python
# -*- coding: utf-8 -*-

from codecs import open
from os import path
from setuptools import setup, find_packages

from req_update import req_update


# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='req-update',

    version=req_update.__version__,

    description='Req Update',
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/albertyw/req-update',

    author='Albert Wang',
    author_email='git@albertyw.com',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Topic :: Software Development :: Version Control',

         'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',

        'Typing :: Typed',
    ],

    keywords='',

    package_data={"req_update": ["py.typed"]},
    packages=find_packages(exclude=["tests"]),

    py_modules=["req_update.req_update"],

    install_requires=[],

    test_suite="req_update.tests",

    # testing requires flake8 and coverage but they're listed separately
    # because they need to wrap setup.py
    extras_require={
        'dev': [],
        'test': [],
    },

    entry_points={
        'console_scripts': [
            'req_update=req_update.req_update:main',
        ],
    },
)
