class ProduceErrors():
    def raiseError(self):
        raise CustomError("error bitch")

class CustomError(Exception):
    def __init__(self, message):
        self.message = message

class AnotherClass(): 
    def __init__(self, produceErrors): 
        self.p = produceErrors
    
    def raiseError(self):
        self.p.raiseError()

Ac = AnotherClass(ProduceErrors())
while True:
    try:
        while True: 
            while True:
                Ac.raiseError()
    except CustomError:
        break 