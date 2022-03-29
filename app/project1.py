import app.core.plugins as plug
import app.core.simulation as sim
import app.core.app as application
import app.core.script as script

LOAD_ORDER=0

def is_ported(element:sim.SimElement):
    try:
        ports=element.ports
        return len(ports)!=-1
    except:
        return False
  

class Cable():
    '''
        Class that store information about a connection.
    '''
    def __init__(self,port1,port2):
        self.ports=[port1,port2] #Ports which the cable is connected
        self.data=False  #Bit sending by the cable
        self.transmitting=False #True if the cable is transmitting a signal
        
        self.ports[0].cable=self.ports[1].cable=self

class Port():
    '''
        Class that store information about the port of an element.
    '''
    def __init__(self,element,id):
        self.element:sim.SimElement=element #Element owner of this port
        self.id=id #Number/Text that identifies this port
        self.cable:Cable=None #Cable connected to this port

    def __str__(self):
        return str(self.element)+'_'+str(self.id)

def resolve_port(name:str,sim_context:sim.SimContext)->Port:
    return next((port for e in (e for e in sim_context.elements if is_ported(e)) for port in e.ports if str(port)==name),None)
  
class PC(sim.SimElement):
    '''
        Class that represents a host in the simulation.
    '''
    def __init__(self,name,sim_context : sim.SimContext,*args,**kwargs):
        sim.SimElement.__init__(self,name,sim_context)
        self.port=Port(self,1) #Port of the pc
        self.ports=[self.port] #Compat with hub
        self.transmitting=False #True if the host is transmitting a signal

    @classmethod
    def get_element_type_name(cls):
        return "pc"
    
    def update(self):
        pass

class CreateCMD(script.CommandDef):
    def run(self,sim_context:sim.SimContext,type_n,name,*args):
        sim_context.elements.append(sim_context.app.elements[type_n](name,sim_context,*args))

class ConnectCMD(script.CommandDef):
    def run(self,sim_context:sim.SimContext,port1,port2,*args):
        port1=resolve_port(port1,sim_context)
        port2=resolve_port(port2,sim_context)
        if (port1 is not None and port2 is not None):
            Cable(port1,port2)
        
class DisconnectCMD(script.CommandDef):
    def run(self, sim_context:sim.SimContext, port, *params):
        port=resolve_port(port,sim_context)
        if(port is not None):
            c=port.cable
            c.ports[0].cable=None
            c.ports[1].cable=None
            del(c)

class Hub(sim.SimElement):
    '''
        Class that represents a hub in the simulation.
    '''
    def __init__(self,name,sim_context:sim.SimContext,ports='4',*args,**kwargs):
        sim.SimElement.__init__(self,name,sim_context)
        ports=int(ports)
        self.ports=[Port(self,i+1) for i in range(ports)] #Create the amount of ports needed
    
    @classmethod
    def get_element_type_name(cls):
        return "hub"
    
    def update(self):
        pass

class BasicInit(plug.PluginInit1):
    def run(self,app:application.Application,*args,**kwargs):
        app.config['signal_time']=10 #default value of signal_time

        #Script preprocessor that remove comments and empty lines
        app.script_pipe.append(lambda s:[l.replace('\n','') for l in s if l.strip() and l.strip()[0]!='#'])

        #Add to the list the elements added by the plugin
        app.elements['host']=app.elements['pc']=PC
        app.elements['hub']=Hub

class CommandsInit(plug.PluginInit1):
    def run(self,app:application.Application,*args,**kwargs):
        #Add commands to the list
        app.commands['create']=CreateCMD()
        app.commands['connect']=ConnectCMD()
        app.commands['disconnect']=DisconnectCMD()
