import sqlite3
import os.path

class Database():
    def __init__(self):
        self.use_extension_file = 'kmt'
        self.data = {} # dbname : { path : path/filename , memory: bool , conn : { namecon : { objcon : objconn1 , cursors : { namecursor : objcursor }} }
    def createConnection(self,filename=None,path=None,memory=False,name=None):
        if not filename:
            return
        
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

    def getAttrString(self, thing):
        if not isinstance(thing, list):
            return None
        types = []
        for t in thing:
            try:
                name,typedef = t
            except Exception as e:
                continue
            if not isinstance(typedef,type):
                continue
            if not isinstance(name,str):
                continue
            if typedef is bool:
                types.append('{} {}'.format(name,'integer'))
            elif typedef is str:
                types.append('{} {}'.format(name,'text'))
            elif typedef is int:
                types.append('{} {}'.format(name,'integer'))
        if types:
            types = ','.join(types)
            return types
        return None

    def createTable(self,conn=None,table=None,attributes=None,overwrite=False):
        if not (table and attributes):
            return None
        if not conn:
            conn = self.getFirstConnectionAvailable()
        extra = ''
        if not overwrite:
            extra = 'if not exists'
        sentence = 'create table {} {}({})'.format(extra,table,self.getAttrString(attributes))
        result = self.execute(what=sentence,conn=conn)
        return result

    def listTables(self,conn=None):
        if not conn:
            conn = self.getFirstConnectionAvailable()
        sentence = 'SELECT name from sqlite_master where type="table"'
        result = self.execute(what=sentence,conn=conn)
        r = []
        for x in result:
            r.append(x[0])
        return r

    def insert(self,table=None,values=None):
        pass
    def update(self,table=None,attributes=None,values=None,where=None):
        pass
    def select(self,table=None,what=None,where=None):
        pass
    def delete(self,table=None,what=None,where=None):
        pass
    def dropTable(self,table=None):
        pass
    def execute(self,what=None,conn=None):
        if not (conn and what):
            return
        result = None
        try:
            cursor = self.getFirstCursorAvailable(conn)
            cursor.execute(what)
            result = cursor.fetchall()
            conn.commit()
        except sqlite3.Error as Err:
            print(Err)
        finally:
            pass
        return result


