import abc
import os
import app.core.app as app
import app.core.script as script

class SimContext:
    '''
        Stores the information of the simulation: the elements in it and their data.
    '''
    def __init__(self,app : app.Application):
        self.elements=[] #List of elements in the simulation
        self.time=0 #Current time of the simulation
        self.p_queue=script.SubCmdQueue() #Priority queue with the sub-commands to execute
        self.app=app #Application where is running the simulation

    def advance(self):
        '''
            Run one step of the simulation.
        '''
        sc=self.p_queue()

        new_time=sc.time

        if new_time!=self.time:
            self.time=new_time
            for e in self.elements:
                e.update(self)
        for guh in self.app.global_updates_hooks:
            if callable(guh):
                guh(sim_context)
        
        for pre_cmd in self.app.pre_command_hooks:
            if callable(pre_cmd):
                pre_cmd(sc,self)
        sc.cmddef(self,sc.params)
        for post_cmd in self.app.post_command_hooks:
            if callable(post_cmd):
                post_cmd(sc,self)

class SimElement(abc.ABC):
    def __init__(self,name,sim_context : SimContext,*args,**kwargs):
        self.name=name #Name of the network element created
        self.context=sim_context #Context of the simulation where the element is

    def __str__(self):
        return self.name

    @classmethod
    @abc.abstractmethod
    def get_element_type_name(cls):
        '''
            Return the kind of network element this class describes.
        '''
        return "generic"

    @abc.abstractmethod
    def update(self):
        '''
            Called each time the time in the simulation changes.
        '''
        pass

    def output(self, text):
        '''
            Add text to the output of the element in the correct file and directory
        '''
        output_dir=self.context.app.output_dir
        output_file=os.path.join(output_dir,self.name+'.txt')

        os.makedirs(output_file,exist_ok=True)
        out=open(output_file,'a+')
        out.write(text+'\n')
        out.close()
