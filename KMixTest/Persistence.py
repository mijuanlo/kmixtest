from .Database import Database

class Persistence():
    def __init__(self, debug=False):
        self.debug = debug
        self.tables = {'Exam': ['id','title'], 'Graphics':['id','base64'], 'Composition':['id','idExam','type','place','txt','img'], 'Question':['id','idExam','title','type','seq','fixed','linked'], 'Answer':['id','idQuestion','idComposition','answer','groupanswer']}
        self.database = Database(debug)
        self.conn = self.database.createConnection('mydb','.')
        self.examName = None
        self.examId = None
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
        
    def addQuestion(self, data=None):
        print('Adding Question')
        if not self.examName:
            self.examName = 'KMixTestExam'
            self.addExam(self.examName)
        if not self.examId and self.examName:
            result = self.database.select(self.conn,'Exam',['id'],['title = "{}"'.format(self.examName)])
            if result:
                self.examId = result.pop()
        if not self.examId:
            raise RuntimeError()
        self.database.insert(self.conn,'Question',[['idExam','title','type','seq','fixed','linked'],[self.examId,data,'tipo',9,1,1]])        

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
        self.database.createTable(self.conn,'Exam',[{'name':'id','type':int,'pk':True},{'name':'title','type':str,'unique':True}])
        self.database.createTable(self.conn,'Graphics',[{'name':'id','type':int,'pk':True},{'name':'base64','type':str}])
        self.database.createTable(self.conn,'Composition',[{'name':'id','type':int,'pk':True},{'name':'idExam','type':int},{'name':'type','type':str},{'name':'place','type':str},{'name':'txt','type':str,'null':True},{'name':'img','type':int,'null':True}],[{'fk':'idExam','tableref':'Exam','ref':'id'},{'fk':'img','tableref':'Graphics','ref':'id'}])
        self.database.createTable(self.conn,'Question',[{'name':'id','type':int,'pk':True},{'name':'idExam','type':int},{'name':'title','type':str},{'name':'type','type':str},{'name':'seq','type':int},{'name':'fixed','type':bool},{'name':'linked','type':bool}],[{'fk':'idExam','tableref':'Exam','ref':'id'}])
        self.database.createTable(self.conn,'Answer',[{'name':'id','type':int,'pk':True},{'name':'idQuestion','type':int},{'name':'idComposition','type':int},{'name':'answer','type':bool,'null':True},{'name':'groupanswer','type':int,'null':True}],[{'fk':'idQuestion','tableref':'Question','ref':'id'},{'fk':'idComposition','tableref':'Composition','ref':'id'}])

