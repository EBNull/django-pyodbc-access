from django.conf import settings
import os, sys
import django.db
from cStringIO import StringIO

import contextlib
import logging

from temp_db import temp_db

@contextlib.contextmanager
def temp_mdb(filename, usingname='_temp_mdb'):
    db_dict = {'ENGINE': 'access.pyodbc', 'OPTIONS': {'driver': 'access'}, 'NAME': filename}
    with temp_db(db_dict, usingname) as u:
        yield u

def inspect_mdb(filename):
    io = StringIO()
    from django.core.management.commands.inspectdb import Command as InspectCommand
    c = InspectCommand()
    c.stdout = io
    with temp_mdb(filename) as using:
        c.handle_noargs(database=using)
    return io.getvalue()

if __name__ == '__main__':
    #NOTE: This fails if DJANGO_SETTINGS_MODULE is not set for obvious reasons.
    print inspect_mdb(os.argv[1])