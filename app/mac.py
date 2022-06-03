from random import randint
from typing import Callable, Dict, List, Tuple
from app.arp import build_arpq, getARPIP, isdataARPR
from app.bitwork import byteFormat, itoil
from app.core.main import SimContext
from app.extensions import execute_command
from app.framing import MAC_BYTESIZE
from app.ip import IP
from app.package import package_build
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
        self.__ip: List[IP] = [(0, 0, 0, 0) for i in range(nports)]
        self.__masks: List[IP] = [(0, 0, 0, 0) for i in range(nports)]
        self.ip_cache: Dict[IP, int] = {}
        self.ip_packages: Dict[IP, Tuple[IP, int, int, int, int]] = {}

        def callback_for_arp(port: List[int]) -> Callable:
            def pure():
                self.__try_read_arpr(port[0])
            return pure

        for i, p in enumerate(self.get_ports()):
            de = p.get_data_eater()
            de.add_frame_end_callback(callback_for_arp([i]))

    def __try_read_arpr(self, port: int) -> None:
        de = self.get_ports()[port].get_data_eater()
        data = de.get_data()
        if isdataARPR(data[0], data[1]):
            ip = getARPIP(data[0], data[1])
            self.ip_cache[ip] = de.get_origin_mac()[0]
            self.__update_address(ip, port)

    def add_package(self, address: IP, origin_ip: IP,
                    origin_mac: int, data: int, data_len: int, port: int) -> None:
        if address == (0, 0, 0, 0):
            return
        self.ip_packages[address] = (
            origin_ip, origin_mac, data, data_len, port)
        self.__update_address(address, port)

    def __update_address(self, address: IP, port: int):
        if address in self.ip_packages.keys():
            if (address in self.ip_cache.keys()):
                self.__launch_package(address)
            else:
                self.__launch_arp(address, port)

    def __launch_package(self, address: IP) -> None:
        if address in self.ip_cache.keys() and \
                address in self.ip_packages.keys():
            data, dlen, port = self.ip_packages[address]
            pkg = package_build(
                self.ip_cache[address], self.get_mac(port),
                address, self.get_ip(port), data, dlen
            )
            execute_command(
                'send',
                self.get_ports()[port],
                itoil(pkg[0], pkg[1])
            )
            self.ip_packages.pop(address)

    def __launch_arp(self, address: IP, port: int) -> None:
        frame = build_arpq(self.get_mac(port), address)
        execute_command(
            'send',
            self.get_ports()[port],
            itoil(frame[0], frame[1])
        )
        execute_command(
            'send',
            self.get_ports()[port],
            itoil(frame[0], frame[1])
        )
        execute_command(
            'send',
            self.get_ports()[port],
            itoil(frame[0], frame[1])
        )

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
