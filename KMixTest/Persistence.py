from .Database import Database

class Persistence():
    def __init__(self):
        self.database = Database()
        conn = self.database.createConnection('mydb','.')
        self.database.createTable(conn,'testtable2',[('id',bool),('t',str),('i',int)])
        self.database.listTables(conn)

