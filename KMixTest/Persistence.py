from .Database import Database

class Persistence():
    def __init__(self, debug=False):
        self.debug = debug
        self.tables = {'Exam': ['id','title'], 'Graphics':['id','base64'], 'Composition':['id','idExam','type','place','txt','img'], 'Question':['id','idExam','title','type','seq','fixed','linked'], 'Answer':['id','idQuestion','idComposition','answer','groupanswer']}
        self.database = Database(debug)
        self.conn = self.database.createConnection('mydb','.')
        self.examName = None
        self.create_schema()
        if self.check_schema():
            if self.debug:
                print('Schema valid')
        else:
            if self.debug:
                print('Schema not valid')

    def addExam(self,title=None):
        print('Adding Exam')
        if not title:
            title = 'KMixTestExam'
        self.database.insert(self.conn,'Exam',[['title'],[title]])
        
    def addQuestion(self):
        print('Adding Question')
        if not self.examName:
            self.examName = 'KMixTestExam'
            self.addExam(self.examName)
        

    def addAnswer(self):
        print('Adding Answer')

    def check_schema(self):
        tables = self.database.listTables(self.conn)
        for t in self.tables:
            if t not in tables:
                return False
            fields = self.database.getFields(self.conn,t)
            tablefields = self.tables.get(t)
            for x in tablefields:
                if x not in fields:
                    if self.debug:
                        print('{} not in table {}'.format(x,t))
                    return False
            for x in fields:
                if x not in tablefields:
                    if self.debug:
                        print('{} in {}, not used'.format(x,t))
                    return False        
        return True

    def create_schema(self):
        self.database.createTable(self.conn,'Exam',[('id',int,True),('title',str)])
        self.database.createTable(self.conn,'Graphics',[('id',int,True),('base64',str)])
        self.database.createTable(self.conn,'Composition',[('id',int,True),('idExam',int),('type',str),('place',str),('txt',str,False,False,True),('img',int,False,False,True)],[('idExam','Exam','id'),('img','Graphics','id')])
        self.database.createTable(self.conn,'Question',[('id',int,True),('idExam',int),('title',str),('type',str),('seq',int),('fixed',bool),('linked',bool)],[('idExam','Exam','id')])
        self.database.createTable(self.conn,'Answer',[('id',int,True),('idQuestion',int),('idComposition',int),('answer',bool,False,False,True),('groupanswer',int,False,False,True)],[('idQuestion','Question','id'),('idComposition','Composition','id')])

