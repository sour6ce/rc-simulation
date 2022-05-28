from typing import List
from app.core.main import Application, CommandDef, PluginInit1, SimContext, SimElement
from app.ported import PortedElement, delete_element, get_port_byname, isported
from app.exceptions import InvalidScriptParameter, MissingElement
from app.bitwork import itoil, uint
from app.port import Port
import app.extensions as sime
from app.timer import Timer


class BlankCMD(CommandDef):
    def run(self, sim_context, *params):
        pass


class SendCMD(CommandDef):
    def run(self, sim_context: SimContext, host: PortedElement | str, data: str | List[int] | List[bool], *params):
        if not isinstance(host, PortedElement):
            host = sime.get_element_byname(str(host))
        if (host is None):
            raise InvalidScriptParameter(MissingElement(host))
        if not isported(host):
            raise InvalidScriptParameter(
                f"{host} doesn't have ports to send data")
        if host.issending(0):
            sime.schedule_command(
                Application.instance.config['signal_time'], 'send',
                host.name, data, *params, early=False
            )
            return
        if len(data) == 0:
            host.end_sending(0)
            return
        l = itoil(uint(data), len(data))

        timer: SimElement
        name = ['send_timer_host_'+host.name]

        def update_sending():
            host.end_sending(0)
            if len(l) > 0:
                sime.execute_command(
                    'send',
                    host,
                    ''.join(('1' if (v == True) or (
                        v > 0) else '0' for v in l[1:])),
                    *params
                )
            delete_element(name[0])

        timer: Timer = sime.create_element(
            'timer', name[0],
            Application.instance.config['signal_time']
        )
        timer.add_time_passed_callback(update_sending)

        host.send(0, l[0] > 0)


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
