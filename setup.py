#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python packaging."""
import os

from setuptools import setup, find_packages

#: Absolute path to directory containing setup.py file.
here = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(here, 'README.rst')).read()
VERSION = open(os.path.join(here, 'VERSION')).read().strip()

REQUIREMENTS = [
    'Django>=1.11,<2.1',
    'django-anysign>=1.2',
    'requests',
    'requests_oauthlib',
    'pytest-django',
    'pytest-cov',
    'pytest-mock'
]

if __name__ == '__main__':  # Do not run setup() when we import this module.
    setup(
        name='django-adobesign',
        version=VERSION,
        description='Django application to manage online signature with '
                    'AdobeSign.',
        long_description=README,
        classifiers=[
            "Operating System :: POSIX",
            'Framework :: Django',
            'Framework :: Django :: 1.11',
            'Framework :: Django :: 2.0',
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
        ],
        keywords='peopledoc anysign adobesign',
        author='Peopledoc',
        author_email='david.steinberger@people-doc.com',
        url='http://github.com/peopledoc/django-adobesign',
        packages=find_packages(exclude=['demo']),
        include_package_data=True,
        zip_safe=True,
        install_requires=REQUIREMENTS,
    )
