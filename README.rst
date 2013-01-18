================================
MS Jet/Access backend for django
================================

This project implements a MS Access / MS Jet backend for django, so you can use your legacy MS Access project in django. From a design standpoint, you should really be using this as a stepping stone to migrate to a different, fully-supported database backend for django. That said, this should work fine in the interim, and should be a big help in liberating your data from your Access DB.

Why?!?!
=======

Having data stuck in a legacy MS Access system is terrible, but a serious epidemic. An immediate migration away is not always feasable due to legacy software.

Modifications
=============
This project was originally cloned via hg clone https://bitbucket.org/jkafader/django-pyodbc-access/.
When I started to use it, it didn't work out of the box for MS Access. This repository changes the module to work specificly with
MS Access, without trying to maintain compatability with related technologies (like MS SQL Server).

Known Issues
============
- LIMIT queries are plain disabled. If you want to fix this, see base.py.
- Access is bad at this (tm). For example, a query that uses __in can fail if given too many ids. Using a join worked.

Unknown Issues
==============
- Expect a lot

Known Working
=============
- Basic info retreival

  - Model.objects.all()
  
- Foreign Keys

  - ModelInstance.related_object.field
  
  - ModelInstance.related_object_set.all()
  
- Simple Joins

  - Model.objects.exclude(rel__in=RelObj.objects.all())

Changes from upstream
=====================
- Dropped support for anything except MDB files
- Dropped support for anything < Django 1.4
- Default driver is MS Access
- Specification of filenames in DATABASE config instead of a system DSN

How to use it
=============

1. Install pyodbc
-----------------

download and install from source or::

    easy_install pyodbc

2. Clone the repository and add it to your python path
------------------------------------------------------

clone this repository and copy (or add) the "access" directory to your python path.

3. Edit your settings.py file for your project
----------------------------------------------

change your DATABASES settings::

    DATABASES = {
        'default': {
            'ENGINE': 'access.pyodbc',
            'NAME': 'mydatabase.mdb',
            'USER': 'admin',
            'PASSWORD': '',
        }
    }

5. Introspect your DB
---------------------

Presumably, you are working on a legacy project (why else use Access?). Use::

    python manage.py inspectdb

to introspect your database and create a new models.py

Alternatively, add 'access' to your INSTALLED_APPS and introspect any random MDB::

    python manage.py inspect_mdb C:\Path\To\database.mdb

Before doing these steps, if your db has 'relations', you may want to grant permission to admin to view them.
This will let the code detect foreign keys during introspection. To do this, you need to turn on 'Show System Objects' and grant
'Read Data' to admin on 'MSysRelationships'. Doing this varies based on MS Access version.


Known Access Issues
============

* MS Access limits queries to 128 columns. This is a hard limit imposed by the Jet backend. This should hopefully be enough for simple projects, but very complex JOINs may have issues.
* MS Access limits the number of entries in a IN clause
