from .Config import _

AllowedQuestionTypes = ["Single question","Test question","Join activity"]
TranslatedQuestionTypes = [_("Single question"),_("Test question"),_("Join activity")]

class Question():
    counter = [0]
    types = {}
    def __init__(self,name=None):
        if not name:
            for x in AllowedQuestionTypes:
                Question(x)
            return None
        id_name = name.lower().replace(" ","_")
        if id_name not in self.types:
            self.types.setdefault(id_name,self)
            self.id_name = id_name
            self.translated_name = TranslatedQuestionTypes[AllowedQuestionTypes.index(name)]
        else:
            return None
        self.counter[0] += 1
        self.id = self.counter[0]
        self.name = name
        return None
    def getName(self):
        return self.name
    def getTranslatedName(self):
        return self.translated_name
    def getId(self):
        return self.id
    def getNameId(self):
        return self.id_name
    def search(self,oid):
        if isinstance(oid,str):
            for k,v in self.types.items():
                if k == oid:
                    return v
                if v.name == oid:
                    return v
            return None
        elif isinstance(id,int):
            for k,v in self.types.items():
                if v.id == id:
                    return v
            return None
        else:
            raise ValueError()
    def allTypes(self):
        return [ k for k,v in self.types.items() ]
    def allNames(self):
        return [ v.name for k,v in self.types.items() ]
    def allTranslatedNames(self):
        return [ v.translated_name for k,v in self.types.items() ]
    def allIds(self):
        return [ v.id for k,v in self.types.items() ]