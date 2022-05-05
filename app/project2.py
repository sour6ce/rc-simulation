import abc
from random import randint
import app.core.plugins as plug
import app.core.simulation as sim
import app.core.app as app
import app.core.script as script

LOAD_ORDER=1

MAC_BYTESIZE=16
DATASIZE_BYTESIZE=8
VALIDATIONSIZE_BYTESIZE=8

def btoh(data:str):
    return hex(int(data,2))[2:].upper()

def htob(data:str):
    return bin(int(data,16))

#Internet Checksum Implementation
# https://github.com/mdelatorre/checksum/blob/master/ichecksum.py
# https://datatracker.ietf.org/doc/html/rfc1071
def chksum(data:str) -> str:
    data=data[:]
    d_len=len(data)
    # #Put zeros in the back until reach a multiple of 8(looking forfull bytes)
    # if ((d_len%8)!=0):
    #     data=''.join([data,''.join(('0'for i in range(8-(d_len%8)) ))])
    #     d_len=((d_len//8)+1)*8
        
    #Separate for byte and turn it into int
    data=[int(c,16) for c in data]
    # data=[int(data[i:i+8],) for i in range(0,d_len,8)]
    # d_len=d_len//8
    
    sum=0
    
    # make 16 bit words out of every two adjacent 8 bit words in the packet
    # and add them up
    for i in range(0,d_len,2):
        if i + 1 >= d_len:
            sum += (data[i]) & 0xFF
        else:
            w = (((data[i]) << 8) & 0xFF00) + ((data[i+1]) & 0xFF)
            sum += w

    # take only 16 bits out of the 32 bit sum and add up the carries
    while (sum >> 16) > 0:
        sum = (sum & 0xFFFF) + (sum >> 16)

    # one's complement the result
    sum = ~sum

    return sum & 0xFFFF
        

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
            one=self.get_write_cable().sending_one()
            self.__write_cable.end()
            pe:PortedElement=self.get_connected_port().get_element()
            pe.__class__=PortedElement
            pe.on_data_end(self.get_connected_port(),one)
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
    
    def has_port(self,port:Port) -> bool:
        return next((p for p in self.__ports if p==port),None)!=None
    
    @abc.abstractmethod
    def on_data_receive(self,port:Port,one:bool):
        '''
            Called each time the element get some data through some port
        '''
        pass
    
    @abc.abstractmethod
    def on_data_end(self,port:Port,one:bool):
        '''
            Called each time the element stop getting data through some port
        '''
        pass
    
    def send(self,port:Port,one:bool):
        if next((p for p in self.__ports if p==port),None) is not None:
            if one:
                port.send_one()
            else:
                port.send_zero()
                
    def end_sending(self,port:Port):
        if next((p for p in self.__ports if p==port),None) is not None:
            port.end_data()

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
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE],2)*8
        else:
            return None
        
    def get_validation_size(self) -> int:
        if self.__data_size>=MAC_BYTESIZE*2+\
            DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:
            return int(self.__data[MAC_BYTESIZE*2+DATASIZE_BYTESIZE:\
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE],2)*8
        else:
            return None
        
    def get_data(self) -> str:
        data_size=self.get_data_size()
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
        data_size=self.get_data_size()
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
        
    def clear(self):
        self.__finished=False
        self.__reading=False
        self.__data=""
        self.__data_size=0
        self.__expected_size=-1
        
    def put(self,one:bool) -> None:
        if self.isfinished():
            self.clear()
            
        self.__reading=True
        
        if one:
            self.__data+='1'
        else:
            self.__data+='0'
            
        self.__data_size+=1
        
        if self.__expected_size==-1:
            if self.__data_size==MAC_BYTESIZE*2+DATASIZE_BYTESIZE+\
                VALIDATIONSIZE_BYTESIZE:
                self.__expected_size=MAC_BYTESIZE*2+DATASIZE_BYTESIZE+\
                    VALIDATIONSIZE_BYTESIZE+self.get_data_size()*8+\
                        self.get_validation_size()*8
        else:
            if self.__data_size==self.__expected_size:
                self.__finished=True
                
                self._fef()

class PC(PortedElement):
    def __init__(self, name: str, sim_context: sim.SimContext, *args, **kwargs):
        super().__init__(name, sim_context, 1, *args, **kwargs)
        
        self.__mac=''.join([hex(randint(0,15))[2:].upper() for i in range(4)])
        def check_data_end():
            if (self.__de.get_target_mac()==self.get_mac()):
                if (self.__de.iscorrupt()):
                    self.data_output(f"{app.Application.instance.simulation.time}"+\
                        f"{self.__de.get_origin_mac()} {self.__de.get_data()}")
        self.__de=DataEater(check_data_end)
        
    @classmethod
    def get_element_type_name(cls):
        return 'host'
    
    def set_mac(self,mac:str):
        if int(mac,16)<=0xFFFF:
            self.__mac=mac
            
    def get_mac(self)->str:
        return self.__mac[:]
    
    def update(self):
        pass
    
    def on_data_receive(self, port: Port, one: bool):
        self.__de.put(one)
        self.output(f"{self.context.time} {port} send {'1' if one else '0'}")
        
    def on_data_end(self, port: Port,one:bool):
        pass
    
class Hub(PortedElement):
    #NOTE: In cases where to a hub reach 2 or more transmition at the same time
    #each time a transmition reach, schedule an transmition checking for the hub
    #this checking should look for the result of an accumulative XOR of the
    #transmitions then send the data and reset the XOR value, if the checking
    #executes with a reseted XOR value it means that is repeated
    def __init__(self, name: str, sim_context: sim.SimContext, nports: int, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)
        
        self.__data=False
        self.__stacked=False
        
    def on_data_receive(self, port: Port, one: bool):
        if self.has_port(port):
            self.__data=(self.__data and one) or ((not self.__data) and (not one))
            self.__stacked=True
            
            #TODO: Schedule command to check
            
    def check_send(self):
        if self.__stacked:
            self.__stacked=False
            for p in self.get_ports():
                self.send(p,self.__data)
                
    def on_data_receive(self, port: Port, one: bool):
        pass
    
    @classmethod
    def get_element_type_name(cls):
        return 'hub'
    
    def update(self):
        pass

#TODO: Switch class
#TODO: Rewrite Send, Connect, Disconnect commands
#TODO: Mac and SendFrame command classes
#TODO: Hub checking help command
#TODO: Plugin Initialization
#TODO: Data outputing
#TODO: Testing