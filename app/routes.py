from typing import List, Tuple
from app.ip import IP, ip_getnet_ip, iptoi, uip, umask

RouteTableInstance = Tuple[IP, IP, IP, int]


class RouteTable():
    __table: List[RouteTableInstance] = []

    def __init__(self, is_for_host: bool) -> None:
        self.__is_host = is_for_host

    def get_list(self) -> List[RouteTableInstance]:
        return self.__table

    def sort_key(self, instance: RouteTableInstance,) -> int:
        return -(iptoi(instance[1]).bit_count())

    def reset(self) -> None:
        self.__table = []

    def add(
        self,
        destination: IP,
        mask: IP,
        gateway: IP,
        interface: int
    ) -> None:
        t = self.__table
        t.append(
            cast_route(destination, mask, gateway, interface)
        )
        t.sort(key=self.sort_key)
        if self.__is_host:
            if len(t) > 2:
                t = t[-2:]

    def remove(
        self,
        destination: IP,
        mask: IP,
        gateway: IP,
        interface: int
    ) -> None:
        self.__table.remove(
            cast_route(destination, mask, gateway, interface)
        )

    def get_match(self, ip: IP) -> RouteTableInstance | None:
        for tup in self.__table:
            if tup[0] == ip_getnet_ip(ip, tup[1]):
                return tup
        return None


def cast_route(destination, mask, gateway, interface) -> RouteTableInstance:
    return (uip(destination),
            umask(mask),
            uip(gateway),
            int(interface))
