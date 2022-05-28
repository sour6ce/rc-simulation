
from app.core.main import Application, PluginInit1, SimContext
from app.ported import PortedElement
from app.port import Port


class Hub(PortedElement):
    # NOTE: The Hub only send the data of the first transmition that reach
    # it and ignores others, its sended to every port except for the one
    # with the input
    def __init__(self, name: str, sim_context: SimContext,
                 nports: int, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)

        self.__iport: Port = None

        def callback_getter_recieve(port: Port):
            def wrap(one: bool):
                self.on_data_receive(port, one)
            return wrap

        def callback_getter_end(port: Port):
            def wrap(one: bool):
                self.on_data_end(port, one)
            return wrap

        for p in self.get_ports():
            p.add_data_recieve_started_callback(callback_getter_recieve(p))
            p.add_data_recieve_finished_callback(callback_getter_end(p))

    def on_data_receive(self, port: Port, one: bool):
        if self.has_port(port):
            if self.__iport is None or self.__iport == port:
                for p in (prt for prt in self.get_ports() if prt != port):
                    if one:
                        p.send_one()
                    else:
                        p.send_zero()
                self.__iport = port

    def on_data_end(self, port: Port, one: bool):
        if self.has_port(port):
            if self.__iport == port:
                for p in (prt for prt in self.get_ports() if prt != port):
                    p.end_data()
                self.__iport = None

    @classmethod
    def get_element_type_name(cls):
        return 'hub'

    def update(self):
        pass


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.elements['hub'] = Hub
