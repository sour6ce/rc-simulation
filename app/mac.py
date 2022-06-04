from random import randint
from typing import Callable, Dict, List, Tuple, Type
from app.arp import build_arpq, getARPIP, isdataARPR
from app.bitwork import byteFormat, itoil
from app.core.main import SimContext
from app.extensions import execute_command
from app.framing import MAC_BYTESIZE, DataEater
from app.ip import IP, ip_getnet_ip
from app.package import get_package_info, isippkg, package_build
from app.port import Port
from app.ported import PortedElement

BROADCAST_MAC = (1 << (8*MAC_BYTESIZE))-1
BROADCAST_MAC_STR = byteFormat(BROADCAST_MAC, f"$n:{MAC_BYTESIZE*2}")


def is_for_me(my_mac: int, target_mac: int) -> bool:
    return my_mac == target_mac or target_mac == BROADCAST_MAC


class IPDataEater(DataEater):
    def __init__(self,
                 frame_end_feedback: Callable | None = None,
                 data_insertion_feedback: Callable | None = None
                 ):
        super().__init__(frame_end_feedback, data_insertion_feedback)

        self.__ipf = []
        self.add_frame_end_callback(
            lambda: [c() for c in self.__ipf if callable(c)])

    def add_package_arrival_callback(self, call: Callable):
        self.__ipf.append(call)

    def remove_package_arrival_callback(self, call: Callable):
        self.__ipf.remove(call)

    def ispackage(self) -> bool:
        data = self.get_data()
        return isippkg(data[0], data[1])


class MACElement(PortedElement):
    def __init__(self, name: str, sim_context: SimContext,
                 nports: int | str, *args, data_eater_type: Type[IPDataEater] = IPDataEater, **kwargs):
        super().__init__(name, sim_context, nports,
                         data_eater_type=IPDataEater, *args, **kwargs)

        self.__mac = [randint(0, BROADCAST_MAC-1) for i in range(nports)]
        self.__ip: List[IP] = [(0, 0, 0, 0) for i in range(nports)]
        self.__masks: List[IP] = [(0, 0, 0, 0) for i in range(nports)]
        self.ip_cache: Dict[IP, int] = {}
        self.ip_packages: Dict[IP, Tuple[IP, IP, int, int, int, int, int]] = {}

        def callback_for_arp(port: List[int]) -> Callable:
            def pure():
                self.__try_read_arpr(port[0])
            return pure

        def callback_smart_ip_cache(port: List[int]) -> Callable:
            def pure():
                de: IPDataEater = self.get_ports()[port[0]].get_data_eater()
                if (de.ispackage()):
                    data = de.get_data()
                    info = get_package_info(data[0], data[1])
                    origin_ip: IP = info['origin']
                    if ip_getnet_ip(self.get_ip(port[0]), self.get_mask(port[0])) ==\
                            ip_getnet_ip(origin_ip, self.get_mask(port[0])):
                        self.ip_cache[origin_ip] = de.get_origin_mac()[0]
            return pure

        for i, p in enumerate(self.get_ports()):
            de = p.get_data_eater()
            de.add_frame_end_callback(callback_for_arp([i]))
            de.add_frame_end_callback(callback_smart_ip_cache([i]))

    def __try_read_arpr(self, port: int) -> None:
        de = self.get_ports()[port].get_data_eater()
        data = de.get_data()
        if isdataARPR(data[0], data[1]):
            ip = getARPIP(data[0], data[1])
            self.ip_cache[ip] = de.get_origin_mac()[0]
            self.__update_address(ip, port)

    def add_package(self, address: IP, origin_ip: IP, port: int,
                    data: int, data_len: int, halfway_ip: IP | None = None,
                    ttl: int = 0, protocol: int = 0) -> None:
        if address == (0, 0, 0, 0):
            return
        if halfway_ip == None:
            halfway_ip = address
        self.ip_packages[halfway_ip] = (
            address, origin_ip, port, data, data_len, ttl, protocol)
        self.__update_address(halfway_ip, port)

    def __update_address(self, halfway: IP, port: int):
        if halfway in self.ip_packages.keys():
            if (halfway in self.ip_cache.keys()):
                self.__launch_package(halfway)
            else:
                self.__launch_arp(halfway, port)

    def __launch_package(self, halfway: IP) -> None:
        if halfway in self.ip_cache.keys() and \
                halfway in self.ip_packages.keys():
            target, origin_ip, port, data, dlen, ttl, protocol = self.ip_packages[halfway]
            pkg = package_build(
                target_ip=target,
                origin_ip=origin_ip,
                origin_mac=self.get_mac(port),
                target_mac=self.ip_cache[halfway],
                ttl=ttl,
                protocol=protocol,
                data=data,
                data_len=dlen
            )
            execute_command(
                'send',
                self.get_ports()[port],
                itoil(pkg[0], pkg[1])
            )
            self.ip_packages.pop(halfway)

    def __launch_arp(self, ip: IP, port: int) -> None:
        frame = build_arpq(self.get_mac(port), ip)
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

    def set_mac(self, mac: int, port: int | Port = 0) -> None:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            self.__mac[port] = mac

    def get_mac(self, port: int | Port = 0) -> int:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            return self.__mac[port]

    def set_ip(self, ip: IP, port: int | Port = 0) -> None:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            self.__ip[port] = ip

    def get_ip(self, port: int | Port = 0) -> IP:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            return self.__ip[port]

    def set_mask(self, mask: IP, port: int | Port = 0) -> None:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            self.__masks[port] = mask

    def get_mask(self, port: int | Port = 0) -> IP:
        if isinstance(port, Port):
            port = next((i for i, p in enumerate(
                self.__ports) if p == port), -1)
        if port >= 0 and port < len(self.get_ports()):
            return self.__masks[port]
