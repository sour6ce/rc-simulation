from app.exceptions import InvalidScriptParameter, MissingElement
from app.extensions import get_element_with_interface
from app.mac import MACElement
from app.core.main import CommandDef, Application, PluginInit1
from app.ported import PortedElement
from app.ip import uip, umask


class IPCMD(CommandDef):
    def run(self, sim_context, element: str | MACElement, address: str, mask: str, *params):
        address = int(address, 16)
        if not isinstance(element, PortedElement):
            element, interface = get_element_with_interface(str(element))
        if (element is None):
            raise InvalidScriptParameter(MissingElement(element))
        try:
            if interface is None:
                element.set_ip(uip(address))
                element.set_mask(umask(mask))
            else:
                element.set_ip(uip(address), interface-1)
                element.set_mask(umask(mask), interface-1)
        except AttributeError:
            raise InvalidScriptParameter(
                f"{element} doesn't allow mac asignation")
