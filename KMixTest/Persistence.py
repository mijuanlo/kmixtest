from .Database import Database

class Persistence():
    def __init__(self, debug=False):
        self.debug = debug
        self.database = Database(debug)
        self.conn = self.database.createConnection('mydb','.')
        self.create_schema()
        self.database.listTables(self.conn)
    def check_schema(self):
        pass
    def create_schema(self):
        self.database.createTable(self.conn,'Exam',[('id',int,True),('title',str)])
        self.database.createTable(self.conn,'Graphics',[('id',int,True),('base64',str)])
        self.database.createTable(self.conn,'Composition',[('id',int,True),('idExam',int),('type',str),('place',str),('txt',str,False,False,True),('img',int,False,False,True)],[('idExam','Exam','id'),('img','Graphics','id')])
        self.database.createTable(self.conn,'Question',[('id',int,True),('idExam',int),('title',str),('type',str),('seq',int),('fixed',bool),('linked',bool)],[('idExam','Exam','id')])
        self.database.createTable(self.conn,'Answer',[('id',int,True),('idQuestion',int),('idComposition',int),('answer',bool,False,False,True),('groupanswer',int,False,False,True)],[('idQuestion','Question','id'),('idComposition','Composition','id')])

