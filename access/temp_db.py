"""
Allows creation of temporary DB definitions and connections with a new 'using' alias.

Example:

import django.db
from cStringIO import StringIO

def inspect_mdb(filename):
    db_dict = {'ENGINE': 'access.pyodbc', 'OPTIONS': {'driver': 'access'}, 'NAME': filename}
    with temp_db(db_dict, 'test') as using:
        django.db.connections[using].cursor() #Connect immediately
        io = StringIO()
        from django.core.management.commands.inspectdb import Command as InspectCommand
        c = InspectCommand()
        c.stdout = io
        c.handle_noargs(database=using)
    return io.getvalue()

WARNING: You must pass a unique (unused) db alias to temp_db.
WARNING: These db aliases are global across threads (and thus requests) in this process.
         You should use a threadlocal for the alias names and/or base them on the current thread id
         if using this in a request.
    
"""
import django.db
import contextlib

@contextlib.contextmanager
def temp_db(db_dict, usingname='_temp_db'):
    insert_db(db_dict, usingname)
    try:
        yield usingname
    finally:
        remove_db(usingname)

def insert_db(definition, using):
    if using in django.db.connections.databases:
        raise ValueError('%s already exists'%(using))
    if using in django.db.connections:
        raise ValueError('%s already exists'%(using))
    django.db.connections.databases[using] = definition
    return using

def remove_db(using):
    del django.db.connections.databases[using]
    conn = None
    try:
        conn = django.db.connections[using]
        conn.close()
    except Exception:
        pass
    try:
        delattr(django.db.connections._connections, using)
    except Exception:
        pass
    assert not hasattr(django.db.connections._connections, using), "Could not remove database wrapper %s"%(using)