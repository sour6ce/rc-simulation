import abc
from queue import Queue
from random import randint
import app.core.plugins as plug
import app.core.simulation as sim
import app.core.app as app
import app.core.script as script

LOAD_ORDER = 1

MAC_BYTESIZE = 16
DATASIZE_BYTESIZE = 8
VALIDATIONSIZE_BYTESIZE = 8
VALIDATION_BYTESIZE = 16


def schedule_blank(time):
    app.Application.instance.simulation.p_queue.add_early(script.SubCommand(
        time, BlankCMD()))


def complete_bytes(data: str, bytes: int) -> str:
    int(data, 2)
    if (len(data) < bytes*8):
        data = ('0'*((bytes*8)-len(data))) + data
        return data
    else:
        return data[len(data)-(bytes*8):]


def btoh(data: str):
    return hex(int(data, 2))[2:].upper()


def htob(data: str):
    return bin(int(data, 16))

# Internet Checksum Implementation
# https://github.com/mdelatorre/checksum/blob/master/ichecksum.py
# https://datatracker.ietf.org/doc/html/rfc1071


def chksum(data: str) -> str:
    data = data[:]
    d_len = len(data)
    # #Put zeros in the back until reach a multiple of 8(looking forfull bytes)
    # if ((d_len%8)!=0):
    #     data=''.join([data,''.join(('0'for i in range(8-(d_len%8)) ))])
    #     d_len=((d_len//8)+1)*8

    # Separate for byte and turn it into int
    data = [int(data[i:i+2], 16) if i + 1 >= d_len else data[i:]
            for i in range(0, data, 2)]
    # data=[int(data[i:i+8],) for i in range(0,d_len,8)]
    # d_len=d_len//8

    sum = 0

    # make 16 bit words out of every two adjacent 8 bit words in the packet
    # and add them up
    for i in range(0, d_len, 2):
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


def is_ported(element: sim.SimElement) -> bool:
    return element is PortedElement


def resolve_element(element) -> sim.SimElement:
    if isinstance(element, sim.SimElement):
        return element
    else:
        port = resolve_port(element)
        if port is not None:
            return port.get_element()
        else:
            return next((e for e in app.Application.instance.simulation.elements
                         if e.name == str(element)), None)


class Cable():
    def __init__(self, port1, port2) -> None:
        self.__data = False
        self.__transmitting = False

        self.__ports = [resolve_port(port1), resolve_port(port2)]

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


class Port():
    def __init__(self, element: sim.SimElement, id: str) -> None:
        self.__element: sim.SimElement = element
        self.__id = id
        self.__write_cable: Cable = None
        self.__read_cable: Cable = None
        self.__con_port: Port = None

    def isconnected(self) -> bool:
        return not self.__con_port == None

    def connect(self, port) -> bool:
        port: Port = resolve_port(port)
        if self.isconnected() or port.isconnected():
            return False
        wc = app.Application.instance.elements["__Cable"](self, port)
        rc = app.Application.instance.elements["__Cable"](self, port)

        self.__write_cable = port.__read_cable = wc

        self.__read_cable = port.__write_cable = rc

        self.__con_port = port
        port.__con_port = self

        return True

    def disconnect(self) -> bool:
        if not self.isconnected():
            return False
        else:
            self.end_data()
            self.__con_port.end_data()
            del(self.__read_cable)
            del(self.__write_cable)

            self.__read_cable =\
                self.__write_cable =\
                self.__con_port.__read_cable =\
                self.__con_port.__write_cable =\
                self.__con_port.__con_port = None

            return True

    def get_write_cable(self) -> Cable:
        return self.__write_cable

    def get_read_cable(self) -> Cable:
        return self.__read_cable

    def get_connected_port(self):
        return self.__con_port

    def get_element(self) -> sim.SimElement:
        return self.__element

    def __write_data(self, data) -> bool:
        if self.isconnected():
            self.end_data()
            if data:
                self.__write_cable.write_one()
            else:
                self.__write_cable.write_zero()
            pe: PortedElement = self.get_connected_port().get_element()
            pe.__class__ = PortedElement
            pe.on_data_receive(self.get_connected_port(), data)
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

    def end_data(self) -> bool:
        if self.isconnected():
            one = self.get_write_cable().sending_one()
            self.__write_cable.end()
            pe: PortedElement = self.get_connected_port().get_element()
            pe.__class__ = PortedElement
            pe.on_data_end(self.get_connected_port(), one)
            return True
        else:
            return False

    def __str__(self):
        return str(self.__element)+'_'+str(self.id)


class PortedElement(sim.SimElement):
    def __init__(self, name: str, sim_context: sim.SimContext, nports: int, *args, **kwargs):
        sim.SimElement.__init__(self, name, sim_context,
                                nports, *args, **kwargs)

        self.__ports = [Port(self, i+1) for i in range(nports)]

    def get_ports(self):
        return self.__ports.copy()

    def has_port(self, port: Port) -> bool:
        return next((p for p in self.__ports if p == port), None) != None

    @abc.abstractmethod
    def on_data_receive(self, port: Port, one: bool):
        '''
            Called each time the element get some data through some port
        '''
        pass

    @abc.abstractmethod
    def on_data_end(self, port: Port, one: bool):
        '''
            Called each time the element stop getting data through some port
        '''
        pass

    def send(self, port: Port, one: bool):
        if next((p for p in self.__ports if p == port), None) is not None:
            if one:
                port.send_one()
            else:
                port.send_zero()

    def end_sending(self, port: Port):
        if next((p for p in self.__ports if p == port), None) is not None:
            port.end_data()


def resolve_port(port) -> Port:
    if isinstance(port, Port):
        return port
    else:
        next((p for e in (e for e in
                          app.Application.instance.simulation.elements if is_ported(e))
              for p in e.ports if str(port) == str(p)), None)


class DataEater():
    def __init__(self, frame_end_feedback) -> None:
        self._fef = frame_end_feedback
        self.__data = ""
        self.__data_size = 0

        self.__expected_size = -1

        self.__reading = False
        self.__finished = False

    def get_current_data(self) -> str:
        return self.__data

    def __len__(self) -> int:
        return self.__data_size

    def isreading(self) -> bool:
        return self.__reading

    def isfinished(self) -> bool:
        return self.__finished

    def get_header(self) -> str:
        if self.__data_size >= MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:
            return self.__data[0:MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE]
        else:
            return None

    def get_target_mac(self) -> str:
        if self.__data_size >= MAC_BYTESIZE:
            return hex(int(self.__data[0:MAC_BYTESIZE], 2))[2:].upper()
        else:
            return None

    def get_origin_mac(self) -> str:
        if self.__data_size >= MAC_BYTESIZE*2:
            return hex(int(self.__data[MAC_BYTESIZE:MAC_BYTESIZE*2], 2))[2:].upper()
        else:
            return None

    def get_data_size(self) -> int:
        if self.__data_size >= MAC_BYTESIZE*2+DATASIZE_BYTESIZE:
            return int(self.__data[MAC_BYTESIZE*2:
                                   MAC_BYTESIZE*2+DATASIZE_BYTESIZE], 2)*8
        else:
            return None

    def get_validation_size(self) -> int:
        if self.__data_size >= MAC_BYTESIZE*2 +\
                DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:
            return int(self.__data[MAC_BYTESIZE*2+DATASIZE_BYTESIZE:
                                   MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE], 2)*8
        else:
            return None

    def get_data(self) -> str:
        data_size = self.get_data_size()
        if data_size is None:
            return None
        if self.__data_size >=\
            MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE +\
                data_size:
            return hex(int(self.__data[
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE:
                    MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE +
                data_size], 2))[2:].upper()
        else:
            return None

    def get_validation(self) -> str:
        data_size = self.get_data_size()
        validation_size = self.get_validation_size()
        if (data_size is None) or (validation_size is None):
            return None
        if self.__finished:
            return hex(int(self.__data[
                MAC_BYTESIZE*2+DATASIZE_BYTESIZE+VALIDATIONSIZE_BYTESIZE +
                data_size:], 2))[2:].upper()
        else:
            return None

    def iscorrupt(self) -> bool:
        data = self.get_data()
        validation = self.get_validation()
        if validation is None:
            return False
        else:
            return chksum(data) == validation

    def clear(self):
        self.__finished = False
        self.__reading = False
        self.__data = ""
        self.__data_size = 0
        self.__expected_size = -1

    def put(self, one: bool) -> None:
        if self.isfinished():
            self.clear()

        self.__reading = True

        if one:
            self.__data += '1'
        else:
            self.__data += '0'

        self.__data_size += 1

        if self.__expected_size == -1:
            if self.__data_size == MAC_BYTESIZE*2+DATASIZE_BYTESIZE +\
                    VALIDATIONSIZE_BYTESIZE:
                self.__expected_size = MAC_BYTESIZE*2+DATASIZE_BYTESIZE +\
                    VALIDATIONSIZE_BYTESIZE+self.get_data_size()*8 +\
                    self.get_validation_size()*8
        else:
            if self.__data_size == self.__expected_size:
                self.__finished = True

                self._fef()


class PC(PortedElement):
    def __init__(self, name: str, sim_context: sim.SimContext, *args, **kwargs):
        super().__init__(name, sim_context, 1, *args, **kwargs)

        self.__mac = ''.join([hex(randint(0, 15))[2:].upper()
                             for i in range(4)])

        def check_data_end():
            if (self.__de.get_target_mac() == self.get_mac() or
                    self.__de.get_target_mac() == 'FFFF'):
                self.data_output(f"{app.Application.instance.simulation.time}" +
                                 f"{self.__de.get_origin_mac()} {self.__de.get_data()}" +
                                 (f" ERROR" if (self.__de.iscorrupt()) else ""))
        self.__de = DataEater(check_data_end)
        self.__sdata = ""
        self.__timer = 0
        self.__las_update_time = 0

    @classmethod
    def get_element_type_name(cls):
        return 'host'

    def set_mac(self, mac: str):
        if int(mac, 16) <= 0xFFFF:
            self.__mac = mac

    def get_mac(self) -> str:
        return self.__mac[:]

    def update(self):
        newtime = self.context.time
        elapsed = newtime-self.__las_update_time
        self.__las_update_time = newtime

        if self.__sdata != '':
            self.__timer -= elapsed
            if self.__timer == 0:
                data = self.__sdata[0]
                self.__sdata = self.__sdata[1:]
                if data == 1:
                    self.get_ports()[0].send_one()
                else:
                    self.get_ports()[0].send_zero()
                self.__timer =\
                    int(app.Application.instance.config['signal_time'])
                schedule_blank(newtime+self.__timer)
        else:
            if self.__timer == 0:
                self.get_ports()[0].end_data()

    def cast(self, data: str):
        self.__sdata += data
        if self.__timer == 0:
            schedule_blank(self.context.time)

    def on_data_receive(self, port: Port, one: bool):
        self.__de.put(one)
        self.output(
            f"{self.context.time} {port} recieved {'1' if one else '0'}")

    def on_data_end(self, port: Port, one: bool):
        pass


class Hub(PortedElement):
    # NOTE: The Hub only send the data of the first transmition that reach
    # it and ignores others, its sended to every port except for the one
    # with the input
    def __init__(self, name: str, sim_context: sim.SimContext,
                 nports: int, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)

        self.__iport: Port = None

    def on_data_receive(self, port: Port, one: bool):
        if self.has_port(port):
            if self.__iport is None or self.__iport == port:
                for p in (prt for prt in self.get_ports() if prt != port):
                    if one:
                        p.send_one()
                    else:
                        p.send_zero()
                self.__iport = port

    def on_data_end(self, port: Port, one: bool):
        if self.has_port(port):
            if self.__iport == port:
                for p in (prt for prt in self.get_ports() if prt != port):
                    p.end_data()
                self.__iport = None

    @classmethod
    def get_element_type_name(cls):
        return 'hub'

    def update(self):
        pass


class Switch(PortedElement):
    def __init__(self, name: str, sim_context: sim.SimContext,
                 nports: int, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)

        def callable_factory(i: int):
            def r():
                self.__add_dfp_to_q(i)
            return r

        self.__table = {}
        self.__fqueue = Queue()
        self.__current = ['' for i in range(nports)]
        self.__des = [DataEater(callable_factory(i)) for i in range(nports)]
        self.__last_update = 0
        self.__timers = [-1 for i in range(nports)]

    def __add_dfp_to_q(self, index: int):
        de = self.__des[index]
        if de.isfinished():
            if (not de.iscorrupt()):
                port = -1
                if de.get_target_mac() in self.__table.keys():
                    port = self.__table[de.get_target_mac()]
                self.__fqueue.put((de.get_current_data(), port))
                self.__table[de.get_origin_mac()] = index

    def update(self):
        new_time = app.Application.instance.simulation.time
        elapsed = new_time-self.__last_update
        self.__last_update = new_time
        frame, port = self.__fqueue.queue[0]
        can_move_frame = (port == -1 and all((cur == '' for cur in self.__current))) or\
            (self.__current[port] == '')

        if can_move_frame:
            self.__fqueue.get()
            self.__current = [frame if i == port or port == -1 else value
                              for i, value in enumerate(self.__current)]

        self.__timers = [value-elapsed if self.__current[i] != ''
                         else -1 for i, value in enumerate(self.__timers)]

        did_send = False

        for i in range(len(self.get_ports())):
            if self.__current[i] != '':
                if self.__timers[i] == 0:
                    data = self.__current[i][0]
                    self.__current[i] = self.__current[i][1:]
                    if data == 1:
                        self.get_ports()[i].send_one()
                    else:
                        self.get_ports()[i].send_zero()
                    self.__timers[i] =\
                        int(app.Application.instance.config['signal_time'])
                    did_send = True
            else:
                if self.__timers[i] == 0:
                    self.get_ports()[i].end_data()
                    self.__timers[i] -= 1

        if did_send:
            schedule_blank(self.__current[i] +
                           int(app.Application.instance.config['signal_time']))

    def on_data_receive(self, port: Port, one: bool):
        if self.has_port(port):
            de: DataEater = next((self.__des[i] for i, p in
                                 enumerate(self.get_ports()) if p == port))
            de.put(one)

    def on_data_end(self, port: Port, one: bool):
        pass


class BlankCMD(script.CommandDef):
    def run(self, sim_context, *params):
        pass


class InvalidScriptParameters(Exception):
    pass


class MissingElement(Exception):
    pass


class SendCMD(script.CommandDef):
    def run(self, sim_context, host, data, *params):
        host: PC = resolve_element(host)
        if (host is not None):
            host.cast(data)


class Connect(script.CommandDef):
    def run(self, sim_context, port1, port2, *params):
        port1 = resolve_port(port1)
        port2 = resolve_port(port2)
        if (port2 is not None and port1 is not None):
            if (port1.isconnected() or port2.isconnected()):
                raise InvalidScriptParameters(
                    f"At least one of the given ports is already connected")
            port1.connect(port2)
        else:
            raise InvalidScriptParameters(f"Invalid port names passed")


class Disconnect(script.CommandDef):
    def run(self, sim_context, port, *params):
        port = resolve_port(port)
        if (port is not None):
            port.disconnect()
        else:
            raise InvalidScriptParameters(f"Invalid port names passed")


class CreateCMD(script.CommandDef):
    def run(self, sim_context: sim.SimContext, type_n, name, *args):
        if not (type_n in app.Application.instance.elements.keys()):
            raise MissingElement(
                f"{type_n} is not a registered simulation element")
        sim_context.elements.append(
            sim_context.app.elements[type_n](name, sim_context, *args))


class MacCMD(script.CommandDef):
    def run(self, sim_context, host, address, *params):
        int(address, 16)
        host: PC = resolve_element(host)
        if (host is not None):
            host.set_mac(address)


class SendFrameCMD(script.CommandDef):
    def run(self, sim_context, host, mac, data, * params):
        host: PC = resolve_element(host)
        int(mac, 16)
        int(data, 16)
        stream = complete_bytes(htob(mac), MAC_BYTESIZE//8) +\
            complete_bytes(htob(host.get_mac()), MAC_BYTESIZE//8)
        data_len = (len(data)+1)//2
        stream += complete_bytes(bin(data_len), DATASIZE_BYTESIZE//8)
        cs = chksum(data)
        stream += complete_bytes(bin(VALIDATION_BYTESIZE//8),
                                 VALIDATIONSIZE_BYTESIZE//8)
        stream += complete_bytes(htob(data), data_len)
        stream += complete_bytes(bin(cs), VALIDATIONSIZE_BYTESIZE//8)
        app.Application.instance.commands['send'].run(
            sim_context,
            host,
            stream,
            *params)
# TODO: Plugin Initialization
# TODO: Data outputing
#TODO: Testing
