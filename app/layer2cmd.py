from app.core.main import Application, CommandDef, PluginInit1
from app.exceptions import InvalidScriptParameter, MissingElement
from app.extensions import execute_command, get_element_byname, get_element_with_interface
from app.framing import frame_build
from app.host import PC
from app.mac import MACElement
from app.port import Port
from app.ported import isported, PortedElement


class MacCMD(CommandDef):
    def run(self, sim_context, element: str | MACElement, address: str | int, *params):
        address = int(address, 16)
        if not isinstance(element, PortedElement):
            element, interface = get_element_with_interface(str(element))
        if (element is None):
            raise InvalidScriptParameter(MissingElement(element))
        try:
            if interface is None:
                element.set_mac(address)
            else:
                element.set_mac(address, interface-1)
        except AttributeError:
            raise InvalidScriptParameter(
                f"{element} doesn't allow mac asignation")


class SendFrameCMD(CommandDef):
    def run(self, sim_context, host: PC | str, mac: int | str, data: int | str, * params):
        if not isinstance(host, PortedElement):
            host = get_element_byname(str(host))
        if (host is None):
            raise InvalidScriptParameter(MissingElement(host))
        if not isported(host):
            raise InvalidScriptParameter(
                f"{host} doesn't have ports to send data")
        try:
            host.get_mac()
        except AttributeError:
            raise InvalidScriptParameter(
                f"{host} doesn't have mac")
        mac = int(mac, 16)
        data_len = len(data) if isinstance(data, str) else None
        data = int(data, 16)

        frame = frame_build(mac, host.get_mac(), data, (data_len+1)//2)

        execute_command('send', host.name, (frame[0], frame[1]), *params)


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['mac'] = MacCMD()
        app.commands['send_frame'] = SendFrameCMD()
