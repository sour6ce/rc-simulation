from typing import List, Tuple
from app.ip import IP, ip_getnet_ip, iptoi, uip, umask

RouteTableInstance = Tuple[IP, IP, IP, int]


class RouteTable():
    __table: List[RouteTableInstance] = []
    __default:  List[RouteTableInstance] = []

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
        if destination == (0, 0, 0, 0) and mask == (0, 0, 0, 0):
            self.__default = [(destination, mask, gateway, interface)]
            return
        t = self.__table
        if self.__is_host:
            self.__table=[cast_route(destination, mask, gateway, interface)]
        else:
            t.append(
                cast_route(destination, mask, gateway, interface)
            )
            t.sort(key=self.sort_key)

    def remove(
        self,
        destination: IP,
        mask: IP,
        gateway: IP,
        interface: int
    ) -> None:
        if destination == (0, 0, 0, 0) and mask == (0, 0, 0, 0):
            self.__default = []
            return
        self.__table.remove(
            cast_route(destination, mask, gateway, interface)
        )

    def get_match(self, ip: IP) -> RouteTableInstance | None:
        for tup in self.__table:
            if tup[0] == ip_getnet_ip(ip, tup[1]):
                return tup
        return None if len(self.__default) == 0 else self.__default[0]


def cast_route(destination, mask, gateway, interface) -> RouteTableInstance:
    return (uip(destination),
            umask(mask),
            uip(gateway),
            int(interface))
