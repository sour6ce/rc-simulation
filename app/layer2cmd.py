from app.bitwork import itoil
from app.core.main import Application, CommandDef, PluginInit1
from app.exceptions import InvalidScriptParameter, MissingElement
from app.extensions import execute_command, get_element_byname
from app.framing import frame_build
from app.host import PC
from app.ported import isported
from app.project2 import PortedElement


class MacCMD(CommandDef):
    def run(self, sim_context, host: str | PortedElement, address: str | int, *params):
        address = int(address, 16)
        if not isinstance(host, PortedElement):
            host = get_element_byname(str(host))
        if (host is None):
            raise InvalidScriptParameter(MissingElement(host))
        try:
            host.set_mac(address)
        except AttributeError:
            raise InvalidScriptParameter(
                f"{host} doesn't allow mac asignation")


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

        frame = frame_build(mac, host.get_mac(), data, data_len//2)

        execute_command('send', host.name, itoil(frame[0], frame[1]))


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['mac'] = MacCMD()
        app.commands['send_frame'] = SendFrameCMD()
