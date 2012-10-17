from __future__ import unicode_literals

import keyword
import re
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS

from access.inspect_mdb import inspect_mdb

class Command(BaseCommand):
    help = "Introspects the database tables in the given mdb file."

    option_list = BaseCommand.option_list

    requires_model_validation = False

    db_module = 'django.db'
    
    args = '<mdb_filename>'
    
    def handle(self, *args, **options):
        if not args:
            raise CommandError("Need mdb filename")
        try:
            self.stdout.write(inspect_mdb(args[0]))
        except NotImplementedError:
            raise CommandError("Database inspection isn't supported for the currently selected database backend.")
