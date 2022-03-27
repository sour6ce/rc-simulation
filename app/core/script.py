import abc
from collections import deque,Iterable

class CommandDef(abc.ABC):
    @abc.abstractmethod
    def run(self,sim_context,*params):
        pass

    def __call__(self,sim_context,*params):
        self.run(self,sim_context,*params)

class SubCommand():
    def __init__(self,time,cmddef,*params):
        self.time=time #Time expected to execute the subcommand
        self.cmddef=cmddef #Command definition
        self.params=params #Parameters passed to the definition

class SubCmdQueue():
    def __init__(self,ls=None):
        if isinstance(ls, Iterable):
            self.list=list(ls)
        else:
            self.list=list()

    def __call__(self):
        '''
            Get the next sub-command and remove it from the queue.
        '''
        return self.list.pop(0)

    def __iter__(self):
        for n in self.list:
            yield n

    def __len__(self):
        return len(self.list)
    
    def insert(self,index,sub_command):
        '''
            Insert the sub-command in the specified position.
        '''
        return self.list.insert(index,sub_command)

    def remove(self,index):
        '''
            Remove the sub-command in the specified position.
        '''
        return self.list.remove(index)

    def add_early(self,sub_command):
        '''
            Put the sub-command in the queue at first among the ones with the same time.
        '''
        #Find the correct index. In this case, the one where first appear a sub command with equal or higher time
        index=next((index for index,sc in zip(range(len(self.list)),self.list) if (sub_command.time<=sc.time)),len(self.list))
        self.insert(index,sub_command)

    def add_late(self,sub_command):
        '''
            Put the sub-command in the queue at last among the ones with the same time.
        '''
        #Find the correct index. In this case, the one where first appear a sub command with higher time
        index=next((index for index,sc in zip(range(len(self.list)),self.list) if (sub_command.time<sc.time)),len(self.list))
        self.insert(index,sub_command)

    def pop(self):
        '''
            Get the next sub-command and remove it from the queue.
        '''
        return self.list.pop(0)

    def ensure_order(self):
        '''
            Order the sub-command by time. Stable.
        '''
        self.list.sort(key=lambda x:x.time)

class MissingCommandDefinition(Exception):
    pass