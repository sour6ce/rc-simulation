from random import randint
from typing import Tuple
from app.bitwork import byteFormat
from app.core.main import SimContext
from app.framing import MAC_BYTESIZE
from app.ip import IP
from app.port import Port
from app.ported import PortedElement

BROADCAST_MAC = (1 << (8*MAC_BYTESIZE))-1
BROADCAST_MAC_STR = byteFormat(BROADCAST_MAC, f"$n:{MAC_BYTESIZE*2}")


def is_for_me(my_mac: int, target_mac: int) -> bool:
    return my_mac == target_mac or target_mac == BROADCAST_MAC


class MACElement(PortedElement):
    def __init__(self, name: str, sim_context: SimContext, nports: int | str, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)

        self.__mac = [randint(0, BROADCAST_MAC-1) for i in range(nports)]
        self.__ip = [(0, 0, 0, 0) for i in range(nports)]
        self.__masks = [(0, 0, 0, 0) for i in range(nports)]

    def set_mac(self, mac: int, port: int | Port) -> None:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            self.__mac[port] = mac

    def get_mac(self, port: int | Port) -> int:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            return self.__mac[port]

    def set_ip(self, ip: IP, port: int | Port) -> None:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            self.__ip[port] = ip

    def get_ip(self, port: int | Port) -> IP:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            return self.__ip[port]

    def set_mask(self, mask: IP, port: int | Port) -> None:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            self.__masks[port] = mask

    def get_mask(self, port: int | Port) -> IP:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            return self.__masks[port]
