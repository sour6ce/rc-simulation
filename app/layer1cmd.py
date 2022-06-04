from typing import List
from app.core.main import Application, CommandDef, PluginInit1, SimContext, SimElement
from app.ported import PortedElement, get_port_byname, isported
from app.exceptions import InvalidScriptParameter, MissingElement
from app.bitwork import itoil, uint
from app.port import Port
import app.extensions as sime
from app.timer import Timer


class BlankCMD(CommandDef):
    def run(self, sim_context, *params):
        pass


class SendCMD(CommandDef):
    def run(self, sim_context: SimContext, host: PortedElement | Port | str,
            data: str | List[int] | List[bool] | int, portindex: int = 0, *params):
        port = None
        if not isinstance(host, PortedElement):
            if isinstance(host, Port):
                port = host
            else:
                port = get_port_byname(host)
                if port is None:
                    host = sime.get_element_byname(str(host))
                    if not isported(host):
                        raise InvalidScriptParameter(
                            f"{host.name} doesn't have ports to send data")
                    port = host.get_ports()[int(portindex)]
        if (port is None):
            raise InvalidScriptParameter(f"Wasn't given a valid host or port")
        if port.sending() or not port.isconnected():
            sime.schedule_command(
                Application.instance.config['signal_time'], 'send',
                port, data, *params, early=False
            )
            return
        if len(data) == 0:
            port.end_data()
            return
        l = itoil(uint(data), len(data))

        timer: SimElement
        name = ['send_timer_port_'+str(port)]

        def update_sending():
            port.end_data()
            if len(l) > 0:
                sime.execute_command(
                    'send',
                    port,
                    ''.join(('1' if (v == True) or (
                        v > 0) else '0' for v in l[1:])),
                    *params
                )

        timer: Timer = sime.create_element(
            'timer', name[0],
            Application.instance.config['signal_time']
        )
        timer.add_time_passed_callback(update_sending)

        port.send_data(l[0] > 0)


class ConnectCMD(CommandDef):
    def run(self, sim_context, port1: str | Port, port2: str | Port, *params):
        if not isinstance(port1, Port):
            port1 = get_port_byname(str(port1))
        if not isinstance(port2, Port):
            port2 = get_port_byname(str(port2))
        if (port2 is not None and port1 is not None):
            port1.connect(port2)
        else:
            raise InvalidScriptParameter(f"Invalid port names passed")


class DisconnectCMD(CommandDef):
    def run(self, sim_context, port: str | Port, *params):
        if not isinstance(port, Port):
            port1 = get_port_byname(str(port))
        if (port is not None):
            port.disconnect()
        else:
            raise InvalidScriptParameter(f"Invalid port name passed")


class CreateCMD(CommandDef):
    def run(self, sim_context, type_n: str, name: str, *args):
        sime.create_element(type_n, name, *args)


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['send'] = SendCMD()
        app.commands['create'] = CreateCMD()
        app.commands['connect'] = ConnectCMD()
        app.commands['disconnect'] = DisconnectCMD()
