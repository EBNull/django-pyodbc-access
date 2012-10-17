"""
MS SQL Server database backend for Django.
"""
#Django 1.4 required

try:
    import pyodbc as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading pyodbc module: %s" % e)

import re
m = re.match(r'(\d+)\.(\d+)\.(\d+)(?:-beta(\d+))?', Database.version)
vlist = list(m.groups())
if vlist[3] is None: vlist[3] = '9999'
pyodbc_ver = tuple(map(int, vlist))
if pyodbc_ver < (2, 0, 38, 9999):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("pyodbc 2.0.38 or newer is required; you have %s" % Database.version)

from django.db.backends import BaseDatabaseWrapper, BaseDatabaseFeatures, BaseDatabaseValidation
from django.db.backends.signals import connection_created
from django.conf import settings
    
from access.pyodbc.operations import DatabaseOperations
from access.pyodbc.client import DatabaseClient
from access.pyodbc.creation import DatabaseCreation
from access.pyodbc.introspection import DatabaseIntrospection
import os
import warnings

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

DRIVER_ACCESS = 'Microsoft Access Driver (*.mdb)'
DRIVER_FREETDS = 'FreeTDS'
DRIVER_SQL_SERVER = 'SQL Server'
DRIVER_SQL_NATIVE_CLIENT = 'SQL Native Client'

class DatabaseFeatures(BaseDatabaseFeatures):
    uses_custom_query_class = True
    can_use_chunked_reads = False
    #uses_savepoints = True


class DatabaseWrapper(BaseDatabaseWrapper):
    drv_name = None
    driver_needs_utf8 = None

    # Collations:       http://msdn2.microsoft.com/en-us/library/ms184391.aspx
    #                   http://msdn2.microsoft.com/en-us/library/ms179886.aspx
    # T-SQL LIKE:       http://msdn2.microsoft.com/en-us/library/ms179859.aspx
    # Full-Text search: http://msdn2.microsoft.com/en-us/library/ms142571.aspx
    #   CONTAINS:       http://msdn2.microsoft.com/en-us/library/ms187787.aspx
    #   FREETEXT:       http://msdn2.microsoft.com/en-us/library/ms176078.aspx

    def _setup_operators(self, sd):
        self.operators = {
            # Since '=' is used not only for string comparision there is no way
            # to make it case (in)sensitive. It will simply fallback to the
            # database collation.
            'exact': '= %s',
            'iexact': "= UCASE(%s)",
            'contains': "LIKE %s ", #ESCAPE '\\' COLLATE " + collation,
            'icontains': "LIKE UCASE(%s) ", #ESCAPE '\\' COLLATE "+ collation,
            'gt': '> %s',
            'gte': '>= %s',
            'lt': '< %s',
            'lte': '<= %s',
            'startswith': "LIKE %s ", #ESCAPE '\\' COLLATE " + collation,
            'endswith': "LIKE %s ", #ESCAPE '\\' COLLATE " + collation,
            'istartswith': "LIKE UCASE(%s) ", #ESCAPE '\\' COLLATE " + collation,
            'iendswith': "LIKE UCASE(%s) ", #ESCAPE '\\' COLLATE " + collation,

            # TODO: remove, keep native T-SQL LIKE wildcards support
            # or use a "compatibility layer" and replace '*' with '%'
            # and '.' with '_'
            'regex': 'LIKE %s COLLATE ' + sd['options']['collation'],
            'iregex': 'LIKE %s COLLATE ' + sd['options']['collation'],

            # TODO: freetext, full-text contains...
        }

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        
        self._set_configuration(self.settings_dict)
        
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)
        
        self.connection = None

    def _set_configuration(self, settings_dict):
        sd = self._merge_settings(self._fixup_settings_dict(settings_dict))
        if not sd['name']:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('You need to specify NAME in your Django settings file.')
        self._setup_operators(sd)
        self.settings_dict = sd
        
    def _fixup_settings_dict(self, sd):
        new_d = {}
        for k, v in sd.iteritems():
            if k.startswith('DATABASE_'):
                k = k.partition('_')[2]
            new_d[k] = v
        return new_d
        
    def _parse_driver(self, driver):
        shortcuts = {
            None: self._guess_driver(),
            'access': DRIVER_ACCESS,
            'sql': DRIVER_SQL_SERVER,
            'freetds': DRIVER_FREETDS,
        }
        return shortcuts.get(driver, driver)

    def _guess_driver(self):
        return DRIVER_ACCESS

    def _merge_settings(self, settings_dict):
        default_settings = dict(
            #Standard Django settings first
            USER=None,
            PASSWORD=None,
            #Host and port, if applicable
            HOST=None,
            PORT=None,
            #Database name, if applicable
            NAME=None,
        )
        settings = dict(default_settings, **settings_dict)
        default_options = dict(
            MARS_Connection=False,
            datefirst=7,
            unicode_results=False,
            autocommit=False,
            dsn=None,
            host_is_server=False,
            collation='Latin1_General_CI_AS',
            extra_params={},
        )
        settings['OPTIONS'] = dict(default_options, **settings.get('OPTIONS', {}))
        settings['OPTIONS']['driver'] = self._parse_driver(settings['OPTIONS'].get('driver', None))
        rename = dict(
            USER='user',
            PASSWORD='password',
            HOST='host',
            PORT='port',
            NAME='name',
            OPTIONS='options',
        )
        for k, v in rename.iteritems():
            settings[v] = settings[k]
            del settings[k]
        return settings

    def _get_connstring_data(self):
        sd = self.settings_dict
        cd = dict()
            
        if sd['options']['dsn']:
            cd['DSN'] = sd['options']['dsn']
        else:
            cd['DRIVER'] = '{%s}'%(sd['options']['driver'])
            if sd['options']['driver'] == DRIVER_ACCESS:
                #Access can't do network, so NAME should be the filename
                cd['DBQ'] = sd['name']
            else:
                if os.name == 'nt' or (sd['options']['driver'] == 'FreeTDS' and sd['options']['host_is_server']):
                    host = sd['host']
                    if sd['port']:
                        host += ',%s'%(sd['port'])
                        cd['SERVER'] = host
                    else:
                        cd['SERVERNAME'] = host
        if sd['user'] is not None:
            cd['UID']=sd['user']
        if sd['password'] is not None:
            cd['PWD']=sd['password']
        if sd['user'] is True:
            if sd['options']['driver'] in (DRIVER_SQL_SERVER, DRIVER_SQL_NATIVE_CLIENT):
                cd['Trusted_Connection'] = 'yes'
            else:
                cd['Integrated Security'] = 'SSPI'

        if sd['options']['driver'] != DRIVER_ACCESS:
            cd['DATABASE'] = sd['name']

        if sd['options']['MARS_Connection']:
            cd['MARS_Connection']='yes'
            
        if sd['options']['extra_params']:
            cd.update(sd['options']['extra_params'])

        return cd

    def _get_new_connection_kwargs(self):
        z = dict(
            autocommit = self.settings_dict['options']['autocommit'],
        )
        if self.settings_dict['options']['unicode_results']:
            z['unicode_results'] = True
        return z
        
    def _open_new_connection(self):
        connstr = ';'.join(('%s=%s'%(k, v) for k, v in self._get_connstring_data().iteritems()))
        kwargs = self._get_new_connection_kwargs()
        conn = Database.connect(connstr, **kwargs)
        self._on_connection_created(conn)
        return conn
        
    def _on_connection_created(self, conn):
        return
        # Set date format for the connection. Also, make sure Sunday is
        # considered the first day of the week (to be consistent with the
        # Django convention for the 'week_day' Django lookup) if the user
        # hasn't told us otherwise
        #cursor.execute("SET DATEFORMAT ymd; SET DATEFIRST %s" % self.datefirst)
        #if self.ops._get_sql_server_ver(self.connection) < 2005:
        #    self.creation.data_types['TextField'] = 'ntext'

        #if self.driver_needs_utf8 is None:
        #    self.driver_needs_utf8 = True
        #    self.drv_name = self.connection.getinfo(Database.SQL_DRIVER_NAME).upper()
        #    if self.drv_name in ('SQLSRV32.DLL', 'SQLNCLI.DLL', 'SQLNCLI10.DLL'):
        #        self.driver_needs_utf8 = False

            # http://msdn.microsoft.com/en-us/library/ms131686.aspx
            #if self.ops._get_sql_server_ver(self.connection) >= 2005 and self.drv_name in ('SQLNCLI.DLL', 'SQLNCLI10.DLL') and self.MARS_Connection:
                # How to to activate it: Add 'MARS_Connection': True
                # to the DATABASE_OPTIONS dictionary setting
                #self.features.can_use_chunked_reads = True

        # FreeTDS can't execute some sql queries like CREATE DATABASE etc.
        # in multi-statement, so we need to commit the above SQL sentence(s)
        # to avoid this
        #if self.drv_name.startswith('LIBTDSODBC') and not self.connection.autocommit:
            #self.connection.commit()
                
    def _cursor(self):
        if self.connection is None:
            self.connection = self._open_new_connection()
            connection_created.send(sender=self.__class__)
        cursor = self.connection.cursor()
        return CursorWrapper(cursor, self.driver_needs_utf8)


class CursorWrapper(object):
    """
    A wrapper around the pyodbc's cursor that takes in account a) some pyodbc
    DB-API 2.0 implementation and b) some common ODBC driver particularities.
    """
    def __init__(self, cursor, driver_needs_utf8):
        self.cursor = cursor
        self.driver_needs_utf8 = driver_needs_utf8
        self.last_sql = ''
        self.last_params = ()

    def format_sql(self, sql, n_params=None):
        if self.driver_needs_utf8 and isinstance(sql, unicode):
            # FreeTDS (and other ODBC drivers?) doesn't support Unicode
            # yet, so we need to encode the SQL clause itself in utf-8
            sql = sql.encode('utf-8')
        # pyodbc uses '?' instead of '%s' as parameter placeholder.
        if n_params is not None:
            sql = sql % tuple('?' * n_params)
        else:
            if '%s' in sql:
                sql = sql.replace('%s', '?')
        return sql

    def format_params(self, params):
        fp = []
        for p in params:
            if isinstance(p, unicode):
                if self.driver_needs_utf8:
                    # FreeTDS (and other ODBC drivers?) doesn't support Unicode
                    # yet, so we need to encode parameters in utf-8
                    fp.append(p.encode('utf-8'))
                else:
                    fp.append(p)
            elif isinstance(p, str):
                if self.driver_needs_utf8:
                    # TODO: use system encoding when calling decode()?
                    fp.append(p.decode('utf-8').encode('utf-8'))
                else:
                    fp.append(p)
            elif isinstance(p, type(True)):
                if p:
                    fp.append(-1)
                else:
                    fp.append(0)
            elif type(p) == type(1L):
                fp.append(int(p))
            else:
                fp.append(p)
        return tuple(fp)

    def execute(self, sql, params=()):
        self.last_sql = sql
        sql = self.format_sql(sql, len(params))
        params = self.format_params(params)
        self.last_params = params
        return self.cursor.execute(sql, params)

    def executemany(self, sql, params_list):
        sql = self.format_sql(sql)
        # pyodbc's cursor.executemany() doesn't support an empty param_list
        if not params_list:
            if '?' in sql:
                return
        else:
            raw_pll = params_list
            params_list = [self.format_params(p) for p in raw_pll]
        return self.cursor.executemany(sql, params_list)

    def format_results(self, rows):
        """
        Decode data coming from the database if needed and convert rows to tuples
        (pyodbc Rows are not sliceable).
        """
        if not self.driver_needs_utf8:
            return tuple(rows)
        # FreeTDS (and other ODBC drivers?) doesn't support Unicode
        # yet, so we need to decode utf-8 data coming from the DB
        fr = []
        for row in rows:
            if isinstance(row, str):
                fr.append(row.decode('utf-8'))
            else:
                fr.append(row)
        return tuple(fr)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is not None:
            return self.format_results(row)
        return row

    def fetchmany(self, chunk):
        return [self.format_results(row) for row in self.cursor.fetchmany(chunk)]

    def fetchall(self):
        return [self.format_results(row) for row in self.cursor.fetchall()]

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        return getattr(self.cursor, attr)
    
    def __iter__(self):
        return iter(self.cursor)