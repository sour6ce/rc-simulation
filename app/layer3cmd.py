from app.exceptions import InvalidScriptParameter, MissingElement
from app.extensions import get_element_byname, get_element_with_interface
from app.host import PC
from app.mac import MACElement
from app.core.main import CommandDef, Application, PluginInit1
from app.ported import PortedElement, isported
from app.ip import IP, uip, umask
from app.routes import RouteTable


class IPCMD(CommandDef):
    def run(self, sim_context, element: str | MACElement, address: str, mask: str, *params):
        address = uip(address)
        if not isinstance(element, PortedElement):
            element_n, interface = get_element_with_interface(str(element))
        if (element_n is None):
            raise InvalidScriptParameter(MissingElement(element))
        try:
            if interface is None:
                element_n.set_ip(address)
                element_n.set_mask(umask(mask))
            else:
                element_n.set_ip(address, interface-1)
                element_n.set_mask(umask(mask), interface-1)
        except AttributeError:
            raise InvalidScriptParameter(
                f"{element_n} doesn't allow ip asignation")


class SendPacketCMD(CommandDef):
    def run(self, sim_context, host: str | MACElement, address: str, data: str, *params):
        address: IP = uip(address)
        data = (int(data, 16), (len(data)+1)//2)
        if not isinstance(host, PortedElement):
            host = get_element_byname(str(host))
        if (host is None):
            raise InvalidScriptParameter(MissingElement(host))
        if not isported(host):
            raise InvalidScriptParameter(
                f"{host} doesn't have ports to send data")
        try:
            pc: PC = host
            pc.send_package(address, data[0], data[1])
        except AttributeError:
            raise InvalidScriptParameter(
                f"{host} doesn't allow sending packets")


class RouteCMD(CommandDef):
    def run(self, sim_context, op: str, element: str | MACElement,
            dest: IP | str = None, mask: IP | str = None, gateway: IP | str = None,
            interface: int | str = None, *params):
        dest = uip(dest)
        mask = uip(mask)
        gateway = uip(gateway)
        interface = int(interface)
        if not isinstance(element, PortedElement):
            element_n = get_element_byname(element)
        if (element_n is None):
            raise InvalidScriptParameter(MissingElement(element))
        try:
            table: RouteTable = element_n.route_table
            if op == 'add':
                table.add(dest, mask, gateway, interface-1)
            elif op == 'delete':
                table.remove(dest, mask, gateway, interface-1)
            elif op == 'reset':
                table.reset()
        except AttributeError:
            raise InvalidScriptParameter(
                f"{element_n} doesn't have a route table")


class PingCMD(CommandDef):
    def run(self, sim_context, host: str | PC, address: str, *params):
        address: IP = uip(address)
        if not isinstance(host, PC):
            host = get_element_byname(str(host))
        if (host is None):
            raise InvalidScriptParameter(MissingElement(host))
        if not isported(host):
            raise InvalidScriptParameter(
                f"{host} doesn't have ports to send data")
        try:
            pc: PC = host
            pc.ping(address)
        except AttributeError:
            raise InvalidScriptParameter(
                f"{host} doesn't allow sending ICMP messages")


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['ip'] = IPCMD()
        app.commands['send_packet'] = SendPacketCMD()
        app.commands['route'] = RouteCMD()
        app.commands['ping'] = PingCMD()
