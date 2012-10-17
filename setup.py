#!/usr/bin/env python
from distutils.core import setup
setup(
    name = "django_pyodbc_access",
    version = "0.1",
    packages = ['access', 'access.pyodbc', 'access.management', 'access.management.commands', 'access.extra', 'access.management'],
    author='CBWhiz',
    author_email='CBWhiz@gmail.com',
    description='Django Access MDB file database backend. Yes, seriously.',
    long_description='Implements a MS Access backend for Django, so you can use your legacy MS Access database in Django.',
    keywords = "django jet ms access database backend 95 98 2000 2002",
    url = "https://github.com/CBWhiz/django-pyodbc-access",
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Development Status :: 4 - Beta',
      'Environment :: Web Environment',
      'Intended Audience :: Developers',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Framework :: Django',
      'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)