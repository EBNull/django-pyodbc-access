================================
MS Jet/Access backend for django
================================

This project implements a MS Access / MS Jet backend for django, so you can use your legacy MS Access project in django. From a design standpoint, you should really be using this as a stepping stone to migrate to a different, fully-supported database backend for django. That said, this should work fine in the interim, and should be a big help in liberating your data from your Access DB.

Why?!?!
=======

I've run across the problem of having data stuck in a legacy MS Access system more than once. I started a project that *needed* to support some legacy ASP code which was reading/writing to an Access DB, and simultaneously implement complex new features. This was my solution.

How to use it
=============

1. Install pyodbc
-----------------

download and install from source or::

    easy_install pyodbc

2. Clone the repository and add it to your python path
------------------------------------------------------

clone this repository (hg clone https://bitbucket.org/jkafader/django-pyodbc-access/) and copy (or add) the "access" directory to your python path.

3. Set up a System DSN for your Access/Jet Database
---------------------------------------------------

Google "setup system dsn". I'm sure you'll find a guide that will help.

4. Edit your settings.py file for your project
----------------------------------------------

change your DATABASES settings::

    DATABASES = {
        'default': {
            'ENGINE': 'access.pyodbc',
            'NAME': 'YourDatabase' # this MUST correspond to a system DSN.
            'OPTIONS': {
	        'driver': 'Microsoft Access Driver (*.mdb)',
                'dsn': 'YourDatabase'
            }
    }


5. Introspect your DB
---------------------

Presumably, you are working on a legacy project (why else use Access?). Use::

    python manage.py inspectdb

to introspect your database and create a new models.py


Known Issues
============

* MS Access limits queries to 128 columns. This is a hard limit imposed by the Jet backend. This should hopefully be enough for simple projects, but very complex JOINs may have issues.