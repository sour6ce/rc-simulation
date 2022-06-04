from random import randint
from app.core.main import Application, PluginInit1
from app.framing import MAC_BYTESIZE, DataEater
from app.ip import IP, iptostr
from app.mac import IPDataEater, MACElement, is_for_me
from app.package import get_package_info
from app.port import Port
from app.ported import PortedElement
from app.bitwork import byteFormat
from app.routes import RouteTable, get_dict_from_instance

# TODO: Implement protocol


class PC(MACElement):
    def __init__(self, name: str, sim_context, *args, **kwargs):
        super().__init__(name, sim_context, 1, *args, **kwargs)

        def check_data_end():
            de: IPDataEater = self.get_ports()[0].get_data_eater()
            if (is_for_me(self.get_mac(), de.get_target_mac()[0])):
                data_str = byteFormat(
                    de.get_data()[0], f'$n:{(de.get_data()[1]+3)//4}$')
                mac_str = byteFormat(de.get_origin_mac()[
                                     0], f'$n:{(de.get_origin_mac()[1]+3)//4}$')
                self.data_output(f"{Application.instance.simulation.time} " +
                                 f"{mac_str} " +
                                 f"{data_str}" +
                                 (f" ERROR" if (de.iscorrupt()) else ""))
                if (de.ispackage()):
                    data = de.get_data()
                    info = get_package_info(data[0], data[1])
                    ip_str = iptostr(info['origin'])
                    self.output(f"{Application.instance.simulation.time} " +
                                f"{ip_str} " +
                                f"{info['data']}", "_payload")

        port: Port = self.get_ports()[0]

        port.get_data_eater().add_frame_end_callback(check_data_end)

        self.route_table = RouteTable(True)

    def send_package(self, address: IP, data: int, data_len: int, ttl: int = 0, protocol: int = 0):
        match = self.route_table.get_match(address)
        if (match is not None):
            match = get_dict_from_instance(match)
            self.add_package(
                address=address,
                origin_ip=self.get_ip(0),
                port=0,
                data=data,
                data_len=data_len,
                halfway_ip=match['gateway'] if match['gateway'] != (
                    0, 0, 0, 0) else address,
                ttl=ttl,
                protocol=protocol
            )

    @classmethod
    def get_element_type_name(cls):
        return 'host'

    def set_mac(self, mac: int, port: int | Port = 0) -> None:
        return super().set_mac(mac, port)

    def get_mac(self, port: int | Port = 0) -> int:
        return super().get_mac(port)

    def update(self):
        pass


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.elements['pc'] = app.elements['host'] = PC
