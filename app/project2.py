import abc
import app.core.plugins as plug
import app.core.simulation as sim
import app.core.app as app
import app.core.script as script

LOAD_ORDER=1

def is_ported(element:sim.SimElement) -> bool:
    return element is PortedElement
      
def resolve_element(element) -> sim.SimElement:
    if isinstance(element,sim.SimElement):
        return element
    else:
        port=resolve_port(element)
        if port is not None:
            return port.get_element()
        else:
            return next( (e for e in app.Application.instance.simulation.elements \
                if e.name==str(element) ),None)

class Cable():
    def __init__(self,port1,port2) -> None:
        self.__data=False
        self.__transmitting=False
        
        self.__ports=[resolve_port(port1),resolve_port(port2)]
        
    def write_one(self) -> None:
        self.__transmitting=True
        self.__data=True
        
    def write_zero(self) -> None:
        self.__transmitting=True
        self.__data=False
        
    def sending(self) -> bool:
        return self.__transmitting    
        
    def sending_one(self) -> bool:
        return self.__data and self.sending()
    
    def sending_zero(self) -> bool:
        return (not self.__data) and self.sending()
    
    def end(self) -> None:
        self.__transmitting=False
        self.__data=False
        
class Port():
    def __init__(self,element:sim.SimElement,id:str) -> None:
        self.__element:sim.SimElement=element
        self.__id=id
        self.__write_cable:Cable=None
        self.__read_cable:Cable=None
        self.__con_port:Port=None
        
    def isconnected(self) -> bool:
        return not self.__con_port==None   
    
    def connect(self,port) -> bool:
        port:Port=resolve_port(port)
        if self.isconnected() or port.isconnected():
            return False
        wc=app.Application.instance.elements["__Cable"](self,port)
        rc=app.Application.instance.elements["__Cable"](self,port)
        
        self.__write_cable=port.__read_cable=wc
        
        self.__read_cable=port.__write_cable=rc
        
        self.__con_port=port
        port.__con_port=self
        
        return True
    
    def disconnect(self) -> bool:
        if not self.isconnected():
            return False
        else:
            del(self.__read_cable)
            del(self.__write_cable)
            
            self.__read_cable=\
                self.__write_cable=\
                    self.__con_port.__read_cable=\
                        self.__con_port.__write_cable=\
                            self.__con_port.__con_port=None
            
            return True
        
    def get_write_cable(self) -> Cable:
        return self.__write_cable
    
    def get_read_cable(self) -> Cable:
        return self.__read_cable
    
    def get_connected_port(self) -> Port:
        return self.__con_port
    
    def get_element(self) -> sim.SimElement:
        return self.__element
    
    def __write_data(self,data) -> bool:
        if self.isconnected():
            self.end_data()
            if data:
                self.__write_cable.write_one()
            else:
                self.__write_cable.write_zero()
            pe:PortedElement=self.get_connected_port().get_element()
            pe.__class__=PortedElement
            pe.on_data_receive(self.get_connected_port(),data)
            return True
        else:
            return False
    
    def send_one(self) -> bool:
        return self.__write_data(True)
        
    def send_zero(self) -> bool:
        return self.__write_data(False)
    
    def receiving(self) -> bool:
        if self.isconnected():
            return self.__read_cable.sending()
        else:
            return False
        
    def receiving_one(self) -> bool:
        return self.receiving() and self.__read_cable.sending_one()
    
    def receiving_zero(self) -> bool:
        return self.receiving() and self.__read_cable.sending_zero()
    
    def end_data(self) ->bool:
        if self.isconnected():
            self.__write_cable.end()
            pe:PortedElement=self.get_connected_port().get_element()
            pe.__class__=PortedElement
            pe.on_data_end(self.get_connected_port())
            return True
        else:
            return False
    
    def __str__(self):
        return str(self.__element)+'_'+str(self.id)
    
class PortedElement(sim.SimElement):
    def __init__(self,name:str,sim_context : sim.SimContext,nports:int,*args,**kwargs):
        sim.SimElement.__init__(self,name,sim_context,nports,*args,**kwargs)
        
        self.__ports=[Port(self,i+1) for i in range(nports)]
        
    def get_ports(self):
        return self.__ports.copy()
    
    @abc.abstractmethod
    def on_data_receive(self,port:Port,One:bool):
        '''
            Called each time the element get some data through some port
        '''
        pass
    
    @abc.abstractmethod
    def on_data_end(self,port:Port):
        '''
            Called each time the element stop getting data through some port
        '''
        pass

def resolve_port(port) -> Port:
    if isinstance(port,Port):
        return port
    else:
        next( (p for e in (e for e in \
            app.Application.instance.simulation.elements if is_ported(e)) \
                for p in e.ports if str(port)==str(p) ),None)
  