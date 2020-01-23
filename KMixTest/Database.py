import sqlite3
import os.path

class Database():
    def __init__(self, debug=False):
        self.debug = debug
        self.use_extension_file = 'kmt'
        self.data = {} # dbname : { path : path/filename , memory: bool , conn : { namecon : { objcon : objconn1 , cursors : { namecursor : objcursor }} }

    def createConnection(self,filename=None,path=None,memory=False,name=None):
        if not filename:
            raise ValueError()
        
        if path is None or not os.path.exists(path):
            path = '.'
        path = os.path.realpath(path)

        if self.use_extension_file[0] != '.':
            self.use_extension_file = '.' + self.use_extension_file

        dbfilename = '{}/{}{}'.format(path,filename,self.use_extension_file)

        mode = ''
        if memory:
            mode = '?mode=memory'

        conn = sqlite3.connect("file:{}{}".format(dbfilename,mode),uri=True)
        connames = []
        for dbname in self.data:
            for c in self.data.get(dbname).get('conn'):
                connames.append(c)
        if name:
            if name in connames:
                name == None
        if not name:
            i = 0
            while True:
                if str(i) not in connames:
                    name = str(i)
                    break
                i += 1
        conndict = {}
        conndict.setdefault(name,{'objconn': conn, 'cursors': { '0': self.createCursor(conn)}})
        data = { 'path': dbfilename , 'memory': memory , 'conn': conndict }
        self.data.setdefault(filename,data)
        return conn

    def getParentData(self,thing,root=None):
        if root is None:
            root = self.data
        if isinstance(root,dict):
            for x in root:
                result = self.getParentData(thing,root.get(x))
                if not result:
                    continue
                if result is True:
                    return root
                else:
                    return result
        else:
            if type(root) == type(thing) and root == thing:
                return True
            else:
                return False

    def createCursor(self,connection=None):
        if connection:
            return connection.cursor()

    def getDatabase(self,name=None):
        if not name or name not in self.data:
            return self.getFirstDatabaseAvailable()
        database = self.data.get(name)
        return database

    def getFirstDatabaseAvailable(self):
        for dbname in self.data:
            database = self.data.get(dbname)
            if database:
                return database

    def getConnection(self,database=None,attr=None):
        if not database:
            database = self.getFirstDatabaseAvailable()
        if isinstance(attr,sqlite3.Connection):
            return self.getParentData(attr)
        if not attr:
            return self.getFirstConnectionAvailable(database)
        if attr not in database:
            return self.getFirstConnectionAvailable(database)
        connection = database.get('conn').get(attr)
        return connection

    def getFirstConnectionAvailable(self,database=None):
        if not database:
            database = self.getFirstDatabaseAvailable()
        for conname in database.get('conn'):
            connection = database.get('conn').get(conname)
            if connection:
                return connection

    def getCursor(self,connection=None,attr=None):
        if not connection:
            connection = self.getFirstConnectionAvailable()
        if not attr:
            return self.getFirstCursorAvailable(connection)
        if isinstance(attr,sqlite3.Cursor):
            return self.getParentData(attr)
        if attr not in connection:
            return self.getFirstCursorAvailable(connection)
        cursor = connection.get('cursors').get(attr)
        return cursor

    def getFirstCursorAvailable(self,connection=None):
        if not connection:
            connection = self.getFirstConnectionAvailable()
        if isinstance(connection,sqlite3.Connection):
            connection = self.getConnection(attr=connection)
        for namecursor in connection.get('cursors'):
            cursor = connection.get('cursors').get(namecursor)
            if cursor:
                return cursor

    def getStrings(self,thingattr=[],thingconstraint=[]):
        try:
            if thingconstraint:
                return '{},{}'.format(self.getAttrString(thingattr),self.getConstraintString(thingconstraint))
            else:
                return '{}'.format(self.getAttrString(thingattr))
        except Exception as e:
            raise ValueError(e)

    def getConstraintString(self, *args, **kwargs):
        if not kwargs and not args:
            raise ValueError()
        if kwargs and args:
            raise ValueError()
        if not kwargs:
            constrainttxt = []
            for largs in args:
                if not isinstance(largs,list):
                    raise ValueError()
                for larg in largs:
                    constrainttxt.append(self.getConstraintString(**larg))
            return ','.join(constrainttxt)

        fk = kwargs.get('fk',None)
        tableref = kwargs.get('tableref',None)
        ref = kwargs.get('ref',None)

        if not fk or not tableref or not ref:
            raise ValueError()

        return 'FOREIGN KEY({}) REFERENCES {}({})'.format(fk,tableref,ref)
        
    def getAttrString(self,*args,**kwargs):
        if not kwargs and not args:
            raise ValueError()
        if kwargs and args:
            raise ValueError()
        if not kwargs:
            argstxt = []
            for largs in args:
                if not isinstance(largs,list):
                    raise ValueError()
                for larg in largs:
                    argstxt.append(self.getAttrString(**larg))
            return ','.join(argstxt)

        name = kwargs.get('name',None)
        typedef = kwargs.get('type',None)
        pk = kwargs.get('pk',None)
        auto = kwargs.get('auto',None)
        null = kwargs.get('null',None)
        unique = kwargs.get('unique',None)

        if not name or not typedef:
            raise ValueError()
        if not auto:
            auto = False
        if not unique:
            unique = False
        if not pk:
            pk = False
        else:
            unique = True
            auto = True
        if not null:
            null = False
        else:
            unique = False
        
        if not isinstance(typedef,type):
            raise ValueError()
        if not isinstance(name,str):
            raise ValueError()
        
        if typedef is bool or typedef is int:
            typedef = 'integer'
        elif typedef is str:
            typedef = 'text'

        l = list()
        l.append(name)
        l.append(typedef)
        if pk:
            l.append('PRIMARY KEY')
        if auto:
            l.append('AUTOINCREMENT')
        if not null:
            l.append('NOT NULL')
        if unique:
            l.append('UNIQUE')

        return ' '.join(l)

    def createTable(self,conn=None,table=None,attributes=None,constraints=None,overwrite=False):
        if not (table and attributes):
            raise ValueError()
        if not conn:
            conn = self.getFirstConnectionAvailable()
        extra = ''
        if not overwrite:
            extra = 'if not exists'
        sentence = 'create table {} {} ({})'.format(extra,table,self.getStrings(attributes,constraints))
        result = self.execute(what=sentence,conn=conn)
        return result

    def listTables(self,conn=None):
        if not conn:
            conn = self.getFirstConnectionAvailable()
        sentence = 'SELECT name from sqlite_master where type="table"'
        result = self.execute(what=sentence,conn=conn)
        # type|name|tbl_name|rootpage|sql
        r = []
        if result:
            for x in result:
                r.append(x[0])
        return r

    def describeTable(self,conn=None,table=None):
        if not table:
            table=''
        else:
            table='and name = "{}"'.format(table)
        if not conn:
            conn = self.getFirstConnectionAvailable()
        sentence = 'SELECT sql from sqlite_master where type="table" {}'.format(table)
        result = self.execute(what=sentence,conn=conn)
        # type|name|tbl_name|rootpage|sql
        r = []
        if result:
            for x in result:
                r.append(x[0])
        return r
    
    def getFields(self,conn=None,table=None):
        if not table:
            raise ValueError()
        if not conn:
            conn = self.getFirstConnectionAvailable()
        sentence = 'pragma table_info("{}")'.format(table)
        result = self.execute(what=sentence,conn=conn)
        r = []
        # cid|name|type|notnull|dflt_value|pk
        if result:
            for x in result:
                r.append(x[1])
        return r

    def insert(self,conn=None,table=None,values=None):
        if not table or not values:
            raise ValueError()
        if not isinstance(values,list):
            raise ValueError()
        if not conn:
            conn = self.getFirstConnectionAvailable()
        tableitems = self.getFields(conn,table)
        names = []
        vals = []
        for li in values:
            if not isinstance(li,list):
                raise ValueError()
            if len(names) < 1:
                for li2 in li:
                    names.append(li2)
                    if li2 not in names:
                        raise ValueError('Wrong attribute name when inserting')
            else:
                if len(li) != len(names):
                    raise ValueError('Distinct number of values when inserting')
                li = [ '"{}"'.format(x) for x in li ]
                txt = ','.join(li)
                vals.append(txt)
        namestxt = ','.join(names)
        valuestxt = '{}'.format(','.join(vals))
        sentence = 'insert into {} ({}) values ({})'.format(table,namestxt,valuestxt)
        result = self.execute(what=sentence,conn=conn)
        r = []
        if result:
            for x in result:
                r.append(x[0])
        return r

    def update(self,conn=None,table=None,attributes=None,values=None,where=None):
        pass

    def select(self,conn=None,table=None,what=None,where=None):
        if not table or not what:
            raise ValueError()
        if not conn:
            conn = self.getFirstConnectionAvailable()
        
        if isinstance(table,list):
            table = ','.join(table)
        if not isinstance(table,str):
            raise ValueError()
                
        if isinstance(what,list):
            what = ','.join(what)
        if not isinstance(what,str):
            raise ValueError()

        if isinstance(where,list):
            where = ' AND '.join(where)
        if not isinstance(where,str):
            raise ValueError()
        
        sentence = 'select {} from {} where ( {} )'.format(what,table,where)
        result = self.execute(what=sentence,conn=conn)
        r = []
        if result:
            for x in result:
                r.append(x[0])
        return r

    def delete(self,conn=None,table=None,what=None,where=None):
        pass

    def dropTable(self,conn=None,table=None):
        if not table:
            raise ValueError()
        if not conn:
            conn = self.getFirstConnectionAvailable()
        sentence = 'drop table {}'.format(table)
        result = self.execute(what=sentence,conn=conn)
        r = []
        if result:
            for x in result:
                r.append(x[0])
        return r

    def execute(self,what=None,conn=None):
        if not (conn and what):
            raise ValueError()
        result = []
        try:
            if self.debug:
                print("Executing: {}".format(what))
            cursor = self.getFirstCursorAvailable(conn)
            cursor.execute(what)
            result = cursor.fetchall()
            conn.commit()
        except sqlite3.Error as Err:
            print(Err)
        finally:
            pass
        return result


