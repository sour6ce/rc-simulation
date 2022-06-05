from typing import Callable, List, Type
from app.core.main import Application, PluginInit1, SimContext
from app.mac import BROADCAST_MAC, IPDataEater, MACElement, is_for_me
from app.package import get_package_info
from app.routes import RouteTable, get_dict_from_instance


class Router(MACElement):
    def __init__(self, name: str, sim_context: SimContext,
                 nports: int | str, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)

        self.route_table: RouteTable = RouteTable(False)

        def callback_package_handler(port: List[int]) -> Callable:
            def pure():
                self.__handle_package([port[0]])
            return pure

        [p.get_data_eater().add_frame_end_callback(callback_package_handler([i]))
            for i, p in enumerate(self.get_ports())]

    @classmethod
    def get_element_type_name(cls):
        return 'router'

    def update(self):
        pass

    def __handle_package(self, port: List[int]):
        de: IPDataEater = self.get_ports()[port[0]].get_data_eater()
        if not is_for_me(de.get_target_mac()[0], self.get_mac(port[0])) and\
                de.get_target_mac()[1] != BROADCAST_MAC:
            return
        if de.ispackage():
            pkg = get_package_info(*de.get_data())
            address = pkg['target']
            data = pkg['data']
            data_len = (pkg['data_length']+7)//8
            match = self.route_table.get_match(address)
            if (match is not None):
                match = get_dict_from_instance(match)
                self.add_package(
                    address=address,
                    origin_ip=pkg['origin'],
                    port=match['interface'],
                    data=data,
                    data_len=data_len,
                    halfway_ip=match['gateway'] if match['gateway'] != (
                        0, 0, 0, 0) else address,
                    ttl=pkg['ttl'],
                    protocol=pkg['protocol']
                )


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.elements['router'] = Router
