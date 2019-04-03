#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages


def _test_requirements():
    return [
        name.rstrip()
        for name in open('requirements-test.txt').readlines()
    ]


def main():
    setup(
        name='dd-smokeping-py',
        version='0.2.0',
        description='Ping for Datadog',
        author='unagi',
        author_email='ray@ymgch.org',
        packages=find_packages(),
        test_require=_test_requirements(),
        test_suite='nose.collector',
        zip_safe=False,
        include_package_data=True,
    )


if __name__ == '__main__':
    main()
