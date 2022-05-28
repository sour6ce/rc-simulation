class MissingElementDefinition(Exception):
    def __init__(self, element_type_name:str, *args: object) -> None:
        super().__init__(f"Missing {element_type_name} type element definition in the application",*args)
        

class MissingElement(Exception):
    def __init__(self, element_name:str, *args: object) -> None:
        super().__init__(f"Missing element with name {element_name} in the simulation",*args) 
        
class InvalidScriptParameter(Exception):
    pass 