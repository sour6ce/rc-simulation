import abc

class PluginInit1(abc.ABC):
    @abc.abstractmethod
    def run(self,app,*args,**kwargs):
        pass

class PluginInit2(abc.ABC):
    @abc.abstractmethod
    def run(self,app,*args,**kwargs):
        pass

class PluginInit3(abc.ABC):
    @abc.abstractmethod
    def run(self,app,*args,**kwargs):
        pass