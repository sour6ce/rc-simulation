import logging
from typing import Any, Iterable, List, Tuple, Type
from app.core.main import Application, CommandDef, MissingCommandDefinition, PluginInit1, SimContext, SimElement, SubCommand
from app.exceptions import MissingElementDefinition

LOAD_ORDER = -1

def get_element_with_interface(name: str) -> Tuple[SimElement,int|None]:
    interface=None
    ind=name.find(':')
    if ind!=-1:
        interface=int(name[ind+1:])
        name=name[:ind]
    return (get_element_byname(name),interface)

def get_commanddef_byname(name: str) -> CommandDef | None:
    cmd: CommandDef | None = Application.instance.commands[name] if name in \
        Application.instance.commands.keys() else None
    if cmd is None:
        cmd = Application.instance.pv_commands[name] if name in \
            Application.instance.pv_commands.keys() else None

    return cmd


def get_element_type_byname(name: str) -> Type | None:
    return Application.instance.elements[name] if \
        name in Application.instance.elements.keys() else None


def get_elements_byname(name: str) -> Iterable[SimElement]:
    return (e for e in Application.instance.simulation.elements if e.name == name)


def get_element_byname(name: str) -> SimElement | None:
    return next(get_elements_byname(name), None)


def get_elements_bytype(t: Type) -> Iterable[SimElement]:
    return (e for e in Application.instance.simulation.elements if isinstance(e, t))


def get_element_bytype(type: Type) -> SimElement | None:
    return next(get_elements_bytype(type), None)


def create_element(type_name: str, name: str, *params, **kwargs) -> SimElement:
    type_name = str(type_name)
    sim_context = Application.instance.simulation
    element_def: Type | None = get_element_type_byname(type_name)
    if element_def is None:
        raise MissingElementDefinition(type_name)
    sim_context.elements.append(
        element_def(str(name), sim_context, *(str(v) for v in params), **kwargs))
    return sim_context.elements[-1]


def schedule_command(time: int, cmd: str, *params, early=True) -> SubCommand:
    time = Application.instance.simulation.time+int(time)
    cmd = str(cmd)
    sub_cmd = SubCommand(time, get_commanddef_byname(cmd), *params)
    if sub_cmd.cmddef is None:
        raise MissingCommandDefinition("${cmd} command definition not found")
    if early:
        Application.instance.simulation.p_queue.add_early(sub_cmd)
    else:
        Application.instance.simulation.p_queue.add_late(sub_cmd)

    return sub_cmd


def schedule_forced_update(time: int, early=True) -> None:
    time = Application.instance.simulation.time+int(time)
    if next((cmd for cmd in Application.instance.simulation.p_queue.list if
            cmd.time == time), None) is not None:
        return
    if early:
        Application.instance.simulation.p_queue.add_early(SubCommand(
            time, Application.instance.pv_commands['blank']))
    else:
        Application.instance.simulation.p_queue.add_late(SubCommand(
            time, Application.instance.pv_commands['blank']))


def execute_command(name: str, *params: List[Any]) -> None:
    c = get_commanddef_byname(name)

    if (c is None):
        raise MissingCommandDefinition(
            f"Impossible to execute {name}, "+"command definition not found")
    else:
        c.run(Application.instance.simulation, *params)


class WrapperCMD(CommandDef):
    def run(self, sim_context, keyword: str, originalcmd: str, *params: List[str]):
        try:
            if callable(Application.instance.wrap_handler):
                Application.instance.wrap_handler(
                    keyword, originalcmd, *params)
        except AttributeError:
            pass


class PrintCMD(CommandDef):
    def run(self, sim_context: SimContext, msg: str = 'DEBUG_PRINT',
            level: str = '10',  *params):
        logging.log(int(level), msg)


def basic_wrap_handler(keyword: str, originalcmd: str, *params: List[str]):
    execute_command(originalcmd, *params)


class BlankCMD(CommandDef):
    def run(self, sim_context, *params):
        pass


class DebugInit(PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.commands['print'] = PrintCMD()
        app.commands['$'] = WrapperCMD()
        app.pv_commands['blank'] = BlankCMD()

        app.wrap_handler = basic_wrap_handler
