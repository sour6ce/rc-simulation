from app.core.main import Application, PluginInit1


class Cable():
    def __init__(self) -> None:
        self.__data = False
        self.__transmitting = False

    def write_one(self) -> None:
        self.__transmitting = True
        self.__data = True

    def write_zero(self) -> None:
        self.__transmitting = True
        self.__data = False

    def sending(self) -> bool:
        return self.__transmitting

    def sending_one(self) -> bool:
        return self.__data and self.sending()

    def sending_zero(self) -> bool:
        return (not self.__data) and self.sending()

    def end(self) -> None:
        self.__transmitting = False
        self.__data = False

class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.elements['__cable']=Cable