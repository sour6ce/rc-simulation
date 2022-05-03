import abc
import app.core.plugins as plug
import app.core.simulation as sim
import app.core.app as app
import app.core.script as script

LOAD_ORDER=1

MAC_BYTESIZE=16
DATASIZE_BYTESIZE=8
VALIDATIONSIZE_BYTESIZE=8

#TODO: Internet Checksum Implementation
# https://github.com/mdelatorre/checksum/blob/master/ichecksum.py
# https://datatracker.ietf.org/doc/html/rfc1071
def chksum(data:str) -> str:
    pass

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

class DataEater():
    def __init__(self,frame_end_feedback) -> None:
        self._fef=frame_end_feedback
        self.__data=""
        self.__data_size=0
        
        self.__expected_size=-1
        
        self.__reading=False
        self.__finished=False
        
    def get_current_data(self) -> str:
        return self.__data
    
    def __len__(self) -> int:
        return self.__data_size
    
    def isreading(self) -> bool:
        return self.__reading
    
    def isfinished(self) -> bool:
        return self.__finished
    
    def get_header(self) -> str:
        if self.__data_size>=MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:
            return self.__data[0:MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE]
        else:
            return None
    
    def get_target_mac(self) -> str:
        if self.__data_size>=MAC_BYTESIZE:
            return hex(int(self.__data[0:MAC_BYTESIZE],2))[2:].upper()
        else:
            return None
        
    def get_origin_mac(self) -> str:
        if self.__data_size>=MAC_BYTESIZE*2:
            return hex(int(self.__data[MAC_BYTESIZE:MAC_BYTESIZE*2],2))[2:].upper()
        else:
            return None
        
    def get_data_size(self) -> int:
        if self.__data_size>=MAC_BYTESIZE*2+DATASIZE_BYTESIZE:
            return int(self.__data[MAC_BYTESIZE*2:\
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE],2)
        else:
            return None
        
    def get_validation_size(self) -> int:
        if self.__data_size>=MAC_BYTESIZE*2+\
            DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:
            return int(self.__data[MAC_BYTESIZE*2+DATASIZE_BYTESIZE:\
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE],2)
        else:
            return None
        
    def get_data(self) -> str:
        data_size=self.get_data_size()*8
        if data_size is None:
            return None
        if self.__data_size>=\
            MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE+\
                data_size:
            return hex(int(self.__data[\
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:\
                    MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE+\
                        data_size],2))[2:].upper()
        else:
            return None
        
    def get_validation(self) -> str:
        data_size=self.get_data_size()*8
        validation_size=self.get_validation_size()
        if (data_size is None) or (validation_size is None):
            return None
        if self.__finished:
            return hex(int(self.__data[\
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE+\
                        data_size:],2))[2:].upper()
        else:
            return None
        
    def iscorrupt(self) -> bool:
        data=self.get_data()
        validation=self.get_validation()
        if validation is None:
            return False
        else:
            return chksum(data)==validation
        
    def put(self,one:bool) -> None:
        if one:
            self.__data+='1'
        else:
            self.__data+='0'
        #TODO: Update expected size and finish with feedback and
        #restart features
    
    #TODO: Clear buffer method and others

#TODO: Util class to handle progressive reading of frames
#This class should handle frame target check and data validation
#for the element is in (in progress)
#TODO: PC,Hub and Switches classes
#TODO: Rewrite Send, Connect, Disconnect commands
#TODO: Mac and SendFrame command classes
#TODO: Plugin Initialization
#TODO: Data outputing
#TODO: Testing