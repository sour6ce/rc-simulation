from app.timer import Timer
from typing import Iterable, List
from app.core.main import Application, SimContext, SimElement
from app.port import Port
from app.extensions import create_element, get_element_byname
from app.ported import delete_element


def isported(element: SimElement) -> bool:
    try:
        element.get_ports()
        return True
    except AttributeError:
        return False


def get_ports_byname(port: str) -> Iterable[Port]:
    port = str(port)
    return (p for e in Application.instance.simulation.elements if isported(e)
            for p in e.get_ports() if str(p) == port)


def get_port_byname(port: str) -> Port | None:
    return next(get_ports_byname(port), None)


def delete_element(name: str) -> bool:
    element = get_element_byname(name)
    if element is None:
        return False
    if isported(element):
        ports: List[Port] = element.get_ports()
        [p.disconnect() for p in ports]
    Application.instance.simulation.elements.remove(element)
    del(element)
    return True


class PortedElement(SimElement):
    def __init__(self, name: str, sim_context: SimContext, default_ports: int | str, *args, **kwargs):
        SimElement.__init__(self, name, sim_context,
                            default_ports, *args, **kwargs)

        self.__ports = [Port(self.name+'_'+str(i+1))
                        for i in range(int(default_ports))]

        def get_timeout_callback(port: Port):
            def wrap():
                port.get_data_eater().clear()
            return wrap

        def data_timeout_timer(port: Port):
            def wrap():
                old_timer: Timer = None
                try:
                    old_timer = get_element_byname(f"{port}_timeout_timer")
                    old_timer.curent_time
                except:
                    pass
                if (old_timer is not None):
                    delete_element(f"{port}_timeout_timer")
                timer: Timer = create_element(
                    'timer',
                    f"{port}_timeout_timer",
                    Application.config['data_input_timeout']
                )
                timer.add_time_passed_callback(get_timeout_callback(port))
            return wrap

        for port in self.__ports:
            port.add_data_send_started_callback(lambda x: self.output(
                f"{Application.instance.simulation.time} {port} send {'1' if x else '0'}"
            ))
            port.add_data_recieve_started_callback(lambda x: self.output(
                f"{Application.instance.simulation.time} {self} recieve {'1' if x else '0'}"
            ))
            if int(Application.config['data_input_timeout']) >= 0:
                port.add_data_send_finished_callback(data_timeout_timer(port))

    def get_ports(self) -> List[Port]:
        return self.__ports

    def has_port(self, port: Port) -> bool:
        return next((p for p in self.__ports if p == port), None) != None

    def issending(self, port: Port | int) -> bool:
        if isinstance(port, int):
            return self.__ports[port].sending()
        if next((p for p in self.__ports if p == port), None) is not None:
            return port.sending()
        else:
            raise ValueError(f"Port in argument don't belongs to this element")

    def send(self, port: Port | int, one: bool) -> bool:
        if isinstance(port, int):
            if one:
                return self.__ports[port].send_one()
            else:
                return self.__ports[port].send_zero()
        if self.has_port(port):
            if one:
                return port.send_one()
            else:
                return port.send_zero()
        else:
            raise ValueError(f"Port in argument don't belongs to this element")

    def end_sending(self, port: Port) -> bool:
        if isinstance(port, int):
            return self.__ports[port].end_data()
        if self.has_port(port):
            return port.end_data()
        else:
            raise ValueError(f"Port in argument don't belongs to this element")
