from queue import Queue
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
  
def resolve_element(name:str,sim_context:sim.SimContext)->sim.SimElement:
    port=resolve_port(name,sim_context)
    if port is None:
        return next((e for e in sim_context.elements if e.name==name),None)
    else:
        return port.element

class Cable():
    '''
        Class that store information about a connection.
    '''
    def __init__(self,port1,port2):
        self.ports=[port1,port2] #Ports which the cable is connected
        self.data='0'  #Bit sending by the cable
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

class Hub(sim.SimElement):
    '''
        Class that represents a hub in the simulation.
    '''
    def __init__(self,name,sim_context:sim.SimContext,ports='4',*args,**kwargs):
        sim.SimElement.__init__(self,name,sim_context)
        ports=int(ports)
        self.ports=[Port(self,i+1) for i in range(ports)] #Create the amount of ports needed
        self.input_port=-1 #Index of the port used as input
        self.transmitting=False #True if the hub is transmitting a signal
    
    @classmethod
    def get_element_type_name(cls):
        return "hub"
    
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
        
        
def search_root(p:Port)->sim.SimElement:
    if (p.element.get_element_type_name()=='pc'):
        if (p.element.transmitting==True):
            return p.element
        else:
            return None
    else:
        i_port=next(port for port in p.element.ports if port.id==p.element.input_port)
        if i_port is p:
            return None
        else:
           c:Cable=i_port.cable
           next_p=next((p for p in c.ports if p is not i_port))
           return search_root(next_p)

class DisconnectCMD(script.CommandDef):
    def run(self, sim_context:sim.SimContext, port, *params):
        port=resolve_port(port,sim_context)
        if(port is not None):
            c=port.cable
            if (c is not None):
                c.ports[0].cable=None
                c.ports[1].cable=None
                #Must cut the transmition
                if(c.transmitting):
                    leftPort:Port=c.ports[0]
                    rightPort:Port=c.ports[1]
                    
                    el=search_root(leftPort)
                    er=search_root(rightPort)
                    
                    q=Queue()
                    q.put(el if er is None else er)
                    while not q.empty():
                        end_transmition(q,q.get())
                del(c)

def read_data(bfs_q:Queue,e:sim.SimElement):
    if e.get_element_type_name()=='pc':
        e.output(f"{e.context.time} {e.port} recieve {e.port.cable.data}")
    if e.get_element_type_name()=='hub':
        i_port,index=next((port,port.id) for port in e.ports if port.cable.transmitting)
        e.input_port=index
        e.output(f"{e.context.time} {i_port} recieve {i_port.cable.data}")
        bfs_q.put((1,e))
        
def write_data(bfs_q:Queue,e:sim.SimElement):
    if e.get_element_type_name()=='hub':
        i_port=next(port for port in e.ports if port.id==e.input_port)
        data=i_port.cable.data
        out_ports=(port for port in e.ports if port.id!=e.input_port and port.cable is not None and not port.cable.transmitting)
        e.transmitting=True
        for port in out_ports:
            c:Cable=port.cable
            out_port:Port=next((p for p in c.ports if p is not port))
            c.transmitting=True
            c.data=data
            e.output(f"{e.context.time} {port} send {data}")
            bfs_q.put((0,out_port.element))

def end_transmition(bfs_q:Queue,e:sim.SimElement):
    if e.get_element_type_name()=='pc':
        c:Cable=e.port.cable
        if c is not None:
            c.data='0'
            c.transmitting=False
    if e.get_element_type_name()=='hub':
        i_port:Port=next(port for port in e.ports if port.id==e.input_port)
        out_ports=(port for port in e.ports if port.id!=e.input_port and port.cable is not None and port.cable.transmitting)
        if (i_port.cable is not None):
            i_port.cable.data='0'
            i_port.cable.transmitting=False
        e.transmitting=False
        for port in out_ports:
            c:Cable=port.cable
            out_port:Port=next((p for p in c.ports if p is not port))
            bfs_q.put(out_port.element)

class EndSendingCMD(script.CommandDef):
    def run(self, sim_context, host, *params):
        host:PC=resolve_element(host,sim_context)
        q=Queue()
        if host is not None and host.port.cable is not None:
            host.transmitting=False
            out_port:Port=next((p for p in host.port.cable.ports if p is not host.port))
            q.put(out_port.element)
            while not q.empty():
                e=q.get()
                end_transmition(q,e)
    
class SendCMD(script.CommandDef):
    def run(self, sim_context:sim.SimContext, host, data, *params):
        host:PC=resolve_element(host,sim_context)
        data_n=data[0] #Current bit to send
        data_r=None
        #Rest of the bits
        if (len(data)>1):
            data_r=data[1:]
        q=Queue()
        if host is not None and host.port.cable is not None:
            if host.port.cable.transmitting:
                #Delay the current sending a time different for each host
                sim_context.p_queue.add_early(script.SubCommand(
                    sim_context.time+(
                    hash(host.name)
                    %
                    50
                    ),SendCMD(),host.name,data,*params))
                return
            #First step of the sending(BFS)
            host.transmitting=True
            host.port.cable.transmitting=True
            host.port.cable.data=data_n
            host.output(f"{host.context.time} {host.port} send {data_n}")
            out_port:Port=next((p for p in host.port.cable.ports if p is not host.port))
            #The queue starts with the first reciever of the signal in it
            q.put((0,out_port.element))
            while not q.empty():
                op,e=q.get()
                if (op==0):
                    #Read the data that reach the element and puts in the queue the writing action if
                    #it's a hub
                    read_data(q,e)
                else:
                    #Write data among the ports and puts in the queue the reading actions of each reciever
                    #element
                    write_data(q,e)
            #Schedule the rest of the sending and the connection end
            if data_r is not None:
                #Send the rest
                sim_context.p_queue.add_early(script.SubCommand(
                    sim_context.time+sim_context.app.config['signal_time'],
                    SendCMD(),
                    host.name,data_r,
                    *params))
            #Shutdown the transmitting
            sim_context.p_queue.add_early(script.SubCommand(
                sim_context.time+sim_context.app.config['signal_time'],
                EndSendingCMD(),
                host.name,
                *params))
            
                    

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
        app.commands['send']=SendCMD()
        
        app.pv_commands['endsend']=EndSendingCMD()
