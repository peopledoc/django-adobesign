#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python packaging."""
import os

from setuptools import setup, find_packages


#: Absolute path to directory containing setup.py file.
here = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(here)


README = open(os.path.join(here, 'README.rst')).read()
VERSION = open(os.path.join(project_root, 'VERSION')).read().strip()

REQUIREMENTS = [
    'Django~=2.2.27, ~=3.2',
    'django-anysign>=1.2',
    'requests',
    'requests_oauthlib',
    'django-sslserver',
]


if __name__ == '__main__':  # Do not run setup() when we import this module.
    setup(
        name='django-adobesign-demo',
        version=VERSION,
        description='Django application demo to manage online signature with '
                    'AdobeSign.',
        long_description=README,
        classifiers=[
            "Operating System :: POSIX",
            'Framework :: Django',
            'Framework :: Django :: 2.2',
            'Framework :: Django :: 3.2',
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
        ],
        keywords='peopledoc anysign adobesign',
        author='Peopledoc',
        author_email='david.steinberger@people-doc.com',
        url='http://github.com/peopledoc/django-adobesign',
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        install_requires=REQUIREMENTS,
    )
