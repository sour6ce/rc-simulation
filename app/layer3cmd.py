from app.exceptions import InvalidScriptParameter, MissingElement
from app.extensions import get_element_with_interface
from app.mac import MACElement
from app.core.main import CommandDef, Application, PluginInit1
from app.ported import PortedElement
from app.ip import uip, umask


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


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['ip'] = IPCMD()
