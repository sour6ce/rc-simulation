from ast import Call
import logging
from typing import Callable, List
from app.core.main import Application
from app.bitwork import uint
import app.core.main as main
import app.core.main as sim
import app.core.main as plug

LOAD_ORDER = -1


def schedule_forced_update(time: int, early=True) -> None:
    time = Application.instance.simulation.time+int(time)
    if next((cmd for cmd in Application.instance.simulation.p_queue.list if
            cmd.time == time), None) is not None:
        return
    if early:
        Application.instance.simulation.p_queue.add_early(main.SubCommand(
            time, Application.instance.pv_commands['blank']))
    else:
        Application.instance.simulation.p_queue.add_late(main.SubCommand(
            time, Application.instance.pv_commands['blank']))


def execute_command(name: str, *params: List[str]) -> None:
    c: main.CommandDef | None = Application.instance.commands[name] if name in \
        Application.instance.commands.keys() else None
    if c is None:
        c = Application.instance.pv_commands[name] if name in \
            Application.instance.pv_commands.keys() else None

    if (c is None):
        raise main.MissingCommandDefinition(
            f"Impossible to execute {name}, "+"command definition not found")
    else:
        c.run(Application.instance.simulation, *params)


class WrapperCMD(main.CommandDef):
    def run(self, sim_context, keyword: str, originalcmd: str, *params: List[str]):
        try:
            if callable(Application.instance.wrap_handler):
                Application.instance.wrap_handler(
                    keyword, originalcmd, *params)
        except AttributeError:
            pass


class PrintCMD(main.CommandDef):
    def run(self, sim_context: sim.SimContext, msg: str = 'DEBUG_PRINT',
            level: str = '10',  *params):
        logging.log(int(level), msg)


def basic_wrap_handler(keyword: str, originalcmd: str, *params: List[str]):
    execute_command(originalcmd, *params)


class DebugInit(plug.PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['print'] = PrintCMD()
        app.commands['$'] = WrapperCMD()

        app.wrap_handler = basic_wrap_handler
