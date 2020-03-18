# from .Database import Database

# class Persistence():
#     def __init__(self, debug=False):
#         self.debug = debug
#         self.tables = {'Exam': ['id','title'], 'Graphics':['id','base64'], 'Composition':['id','idExam','type','place','txt','img'], 'Question':['id','idExam','title','type','seq','fixed','linked'], 'Answer':['id','idQuestion','idComposition','answer','groupanswer']}
#         self.database = Database(debug)
#         self.newExam()
#         ###
#         #self.conn = self.database.createConnection('mydb2','.')
#         #self.create_schema()

#     def addExam(self,title=None):
#         if not self.conn:
#             return None
#         print('Adding Exam')
#         if not title:
#             title = 'KMixTestExam'
#         self.database.insert(self.conn,'Exam',[['title'],[title]])
        
#     def newExam(self):
#         self.conn = None
#         self.examId = None
#         self.examName = None
#         #remove all
    
#     def loadExam(self,filename):
#         if not filename:
#             raise ValueError()
#         self.conn = self.database.openConnection(dbfilename=filename)
#         if self.check_schema():
#             if self.debug:
#                 print('Schema valid')
#         else:
#             if self.debug:
#                 print('Schema not valid')
#             raise RuntimeError()
#         exams = self.getQuestions(self.conn)
#         return exams

#     def saveExam(self,filename,examData):
#         if not filename:
#             raise ValueError()
#         print('Saving Exam as {}'.format(filename))
#         self.conn = self.database.createConnection(dbfilename=filename)
#         self.create_schema()
#         for x in examData:
#             self.addQuestion(x)

#     def getQuestions(self, conn=None):
#         if not conn and not self.conn:
#             raise ValueError()
#         if not conn:
#             conn = self.conn
#         selection = self.database.select(conn=conn,table='Exam',what=['id','title'],where=[],extra='limit 1')
#         if len(selection) == 1:
#             selection = selection[0]
#         if selection:
#             questions = self.database.select(conn=conn,table='Question',what=['seq','fixed','linked','title','type'],where=['idExam={}'.format(selection[0])],extra='order by seq asc')
#         return questions

#     def addQuestion(self, data=None):
#         if not self.conn:
#             return None
#         print('Adding Question')
#         if not self.examName:
#             self.examName = 'KMixTestExam'
#             self.addExam(self.examName)
#         if not self.examId and self.examName:
#             result = self.database.select(self.conn,'Exam',['id'],['title = "{}"'.format(self.examName)])
#             if result:
#                 self.examId = result.pop()[0]
#         if not self.examId:
#             raise RuntimeError()
#         self.database.insert(self.conn,'Question',[['idExam','title','type','seq','fixed','linked'],[self.examId,data[3],data[4],data[0],int(data[1]),int(data[2])]])        

#     def addAnswer(self):
#         if not self.conn:
#             return None
#         print('Adding Answer')

#     def check_schema(self):
#         if not self.conn:
#             return None
#         tables = self.database.listTables(self.conn)
#         for t in self.tables:
#             if t not in tables:
#                 return False
#             fields = self.database.getFields(self.conn,t)
#             tablefields = self.tables.get(t)
#             for x in tablefields:
#                 if x not in fields:
#                     if self.debug:
#                         print('{} not in table {}'.format(x,t))
#                     return False
#             for x in fields:
#                 if x not in tablefields:
#                     if self.debug:
#                         print('{} in {}, not used'.format(x,t))
#                     return False        
#         return True

#     def create_schema(self):
#         if not self.conn:
#             return None
#         self.database.createTable(self.conn,'Exam',[{'name':'id','type':int,'pk':True},{'name':'title','type':str,'unique':True}])
#         self.database.createTable(self.conn,'Graphics',[{'name':'id','type':int,'pk':True},{'name':'base64','type':str}])
#         self.database.createTable(self.conn,'Composition',[{'name':'id','type':int,'pk':True},{'name':'idExam','type':int},{'name':'type','type':str},{'name':'place','type':str},{'name':'txt','type':str,'null':True},{'name':'img','type':int,'null':True}],[{'fk':'idExam','tableref':'Exam','ref':'id'},{'fk':'img','tableref':'Graphics','ref':'id'}])
#         self.database.createTable(self.conn,'Question',[{'name':'id','type':int,'pk':True},{'name':'idExam','type':int},{'name':'title','type':str},{'name':'type','type':str},{'name':'seq','type':int},{'name':'fixed','type':bool},{'name':'linked','type':bool}],[{'fk':'idExam','tableref':'Exam','ref':'id'}],['idExam','seq'])
#         self.database.createTable(self.conn,'Answer',[{'name':'id','type':int,'pk':True},{'name':'idQuestion','type':int},{'name':'idComposition','type':int},{'name':'answer','type':bool,'null':True},{'name':'groupanswer','type':int,'null':True}],[{'fk':'idQuestion','tableref':'Question','ref':'id'},{'fk':'idComposition','tableref':'Composition','ref':'id'}])

import json
import os

class Persistence():
    def __init__(self,*args,**kwargs):
        pass

    def loadExam(self,filename):
        obj = None
        if not os.path.exists(filename):
            raise ValueError()
        with open(filename,'r') as fp:
            data = fp.read()
        if not data:
            raise ValueError()
        obj = json.loads(data)
        return obj

    def saveExam(self,filename,examData):
        data = json.dumps(examData, separators=(",",":"), sort_keys=True)
        with open(filename,'w') as fp:
            fp.write(data)