from io import TextIOWrapper
import os
import importlib
import inspect
import types
from fnmatch import fnmatch
from collections.abc import Iterable
from collections import deque
import abc
import os
from typing import Dict, List


class Application:
    def __init__(self, app_path):
        self.app_path = app_path  # Main directory of the app
        self.plugins_files = []  # Filenames of all plugins
        self.plugins = []  # Module Python objects of the loaded plugins
        self.first_inits = []  # Initialization classes for the first stage
        self.second_inits = []  # Initialization classes for the second stage
        self.third_inits = []  # Initialization classes for the third stage
        self.commands = {}  # Avaiable commands in the app
        self.pv_commands = {}  # Avaiable private commands in the app
        self.elements = {}  # Avaiable network elements in the app
        self.script_pipe = []  # Script pre-processors loaded
        self.pre_command_hooks = []  # Hooks to execute before commands loaded
        self.post_command_hooks = []  # Hooks to execute after commands loaded
        self.global_updates_hooks = []  # Hooks to execute on update
        
        self.open_files:Dict[str,TextIOWrapper]={}

        self.script_file = "script.txt"  # The filename of the script to execute
        self.script = []  # Each line of the script

        self.config = {}  # Stores configuration values of the app
        # File that will override the configuration setted by plugins
        self.config_file = "config.txt"

        self.output_dir = "output"  # Directory where element output should go

        self.simulation = SimContext(self)  # Current simulation information

        Application.instance = self  # Singleton implementation

    def close_open_files(self):
        for f in self.open_files.values():
            f.close()
        self.open_files.clear()

    def resolve_command(self, cmd_name):
        '''
            Finds the command with the given name, public or private. Used to easy the sub-command creation. Prioritize public.
            Returns False if command is not found.
        '''
        if cmd_name in self.commands.keys() and isinstance(self.commands[cmd_name], CommandDef):
            return self.commands[cmd_name]
        if cmd_name in self.pv_commands.keys() and isinstance(self.pv_commands[cmd_name], CommandDef):
            return self.pv_commands[cmd_name]
        return False

    def scan_plugins(self):
        '''
            Get the scripts filenames from the files in app directory.
        '''
        self.plugins_files = [py for py in os.listdir(os.path.join(self.app_path, "app")) if os.path.isfile(
            os.path.join(os.path.join(self.app_path, "app"), py)) and fnmatch(py, "*.py")]
        return self

    def import_plugins(self):
        '''
            Load the objects defined in app folder.
        '''
        self.plugins = [importlib.import_module("app."+os.path.splitext(
            f)[0]) for f in self.plugins_files]  # TODO: Log errors at loading plugins

        # Order plugins according to the load order defined in them. If it's not defined is assumed that is zero.
        def plugin_lo(p):
            return next((c for n, c in inspect.getmembers(p) if (n == 'LOAD_ORDER')), 0)

        self.plugins.sort(key=plugin_lo)

        # Get initialization classes for each stage
        self.first_inits = [c for plugin in self.plugins for n, c in inspect.getmembers(
            plugin) if inspect.isclass(c) and issubclass(c, PluginInit1) and (not inspect.isabstract(c))]
        self.second_inits = [c for plugin in self.plugins for n, c in inspect.getmembers(
            plugin) if inspect.isclass(c) and issubclass(c, PluginInit2) and (not inspect.isabstract(c))]
        self.third_inits = [c for plugin in self.plugins for n, c in inspect.getmembers(
            plugin) if inspect.isclass(c) and issubclass(c, PluginInit3) and (not inspect.isabstract(c))]
        return self

    def run_init1(self):
        '''
            Run the first stage of initialization of the plugins.
        '''
        for init in self.first_inits:
            init().run(self)
        return self

    def run_init2(self):
        '''
            Run the second stage of initialization of the plugins.
        '''
        for init in self.second_inits:
            init().run(self)
        return self

    def run_init3(self):
        '''
            Run the third stage of initialization of the plugins.
        '''
        for init in self.third_inits:
            init().run(self)
        return self

    def load_script(self):
        '''
            Load the simulation script.
        '''
        if not os.path.isfile(self.script_file):
            raise FileNotFoundError(
                f"Missing {self.script_file} file (script file).")
        f = open(self.script_file, 'r')
        self.script = f.readlines()
        f.close()
        return self

    def run_script_preprocessor(self):
        '''
            Execute every callable preprocessor of script registered by the app.
        '''
        for spp in self.script_pipe:
            if callable(spp):
                self.script = spp(self.script)
        return self

    def compile_script(self):
        '''
            Analyze the script lines and push the commands in the queue to execute.
        '''
        for l in self.script:
            c = l.split(' ')
            time = int(c[0])
            cmd_name = c[1]
            args = []
            if len(c) > 2:
                args = c[2:]

            if cmd_name not in self.commands.keys() or not isinstance(self.commands[cmd_name], CommandDef):
                raise(MissingCommandDefinition(
                    f"{cmd_name} command definition not founded among public commands."))
            else:
                self.simulation.p_queue.add_late(
                    SubCommand(time, self.commands[cmd_name], *args))

    def load_configuration(self):
        '''
            Load the config from the config file. Overrides current stored configuration values.
        '''
        if not os.path.isfile(self.config_file):
            return self
        f = open(self.config_file, 'r')
        lines = f.readlines()
        f.close()

        for l in lines:
            if l.strip() and l.count('=') == 1:
                eq_pos = l.find('=')
                self.config[l[:eq_pos].replace(' ', '_')] = l[eq_pos+1:]
        return self


class SimContext:
    '''
        Stores the information of the simulation: the elements in it and their data.
    '''

    def __init__(self, app: Application):
        self.elements = []  # List of elements in the simulation
        self.time = 0  # Current time of the simulation
        # Priority queue with the sub-commands to execute
        self.p_queue = SubCmdQueue()
        self.app = app  # Application where is running the simulation

    def advance(self):
        '''
            Run one step of the simulation.
        '''
        if len(self.p_queue) == 0:
            return False
        sc = self.p_queue()

        new_time = sc.time

        self.time = new_time
        elements = self.elements.copy()
        for e in elements:
            e.update()
        for guh in self.app.global_updates_hooks:
            if callable(guh):
                guh(self)

        for pre_cmd in self.app.pre_command_hooks:
            if callable(pre_cmd):
                pre_cmd(sc, self)
        sc.cmddef(self, *sc.params)
        for post_cmd in self.app.post_command_hooks:
            if callable(post_cmd):
                post_cmd(sc, self)
        return True


class SimElement(abc.ABC):
    def __init__(self, name, sim_context: SimContext, *args, **kwargs):
        self.name = name  # Name of the network element created
        self.context = sim_context  # Context of the simulation where the element is

    def __str__(self):
        return self.name

    @classmethod
    @abc.abstractmethod
    def get_element_type_name(cls):
        '''
            Return the kind of network element this class describes.
        '''
        return "generic"

    @abc.abstractmethod
    def update(self):
        '''
            Called each time the time in the simulation changes.
        '''
        pass

    def dispose(self):
        pass

    def output(self, text, suffix=''):
        '''
            Add text to the output of the element in the correct file and directory
        '''
        output_dir = self.context.app.output_dir
        output_file = os.path.join(output_dir, self.name+f'{suffix}.txt')
        
        if output_file not in Application.instance.open_files.keys():
            os.makedirs(output_dir, exist_ok=True)
            if os.path.isfile(output_file):
                os.remove(output_file)
            Application.instance.open_files[output_file] = open(output_file, 'a+')
            
        Application.instance.open_files[output_file].write(text+'\n')

    def data_output(self, text):
        self.output(text, suffix='_data')


class CommandDef(abc.ABC):
    @abc.abstractmethod
    def run(self, sim_context, *params):
        pass

    def __call__(self, sim_context, *params):
        self.run(sim_context, *params)


class SubCommand():
    def __init__(self, time, cmddef, *params):
        self.time = time  # Time expected to execute the subcommand
        self.cmddef = cmddef  # Command definition
        self.params = list(params)  # Parameters passed to the definition

    def __str__(self) -> str:
        return (f"{self.time} {type(self.cmddef).name} " + ' '.join(self.params))

    def __repr__(self) -> str:
        return str(self)


class SubCmdQueue():
    def __init__(self, ls=None):
        if isinstance(ls, Iterable):
            self.list = list(ls)
        else:
            self.list = list()

    def __call__(self):
        '''
            Get the next sub-command and remove it from the queue.
        '''
        return self.list.pop(0)

    def __iter__(self):
        for n in self.list:
            yield n

    def __len__(self):
        return len(self.list)

    def insert(self, index, sub_command):
        '''
            Insert the sub-command in the specified position.
        '''
        return self.list.insert(index, sub_command)

    def remove(self, index):
        '''
            Remove the sub-command in the specified position.
        '''
        return self.list.remove(index)

    def add_early(self, sub_command):
        '''
            Put the sub-command in the queue at first among the ones with the same time.
        '''
        # Find the correct index. In this case, the one where first appear a sub command with equal or higher time
        index = next((index for index, sc in zip(range(len(self.list)), self.list) if (
            sub_command.time <= sc.time)), len(self.list))
        self.insert(index, sub_command)

    def add_late(self, sub_command):
        '''
            Put the sub-command in the queue at last among the ones with the same time.
        '''
        # Find the correct index. In this case, the one where first appear a sub command with higher time
        index = next((index for index, sc in zip(range(len(self.list)), self.list) if (
            sub_command.time < sc.time)), len(self.list))
        self.insert(index, sub_command)

    def pop(self):
        '''
            Get the next sub-command and remove it from the queue.
        '''
        return self.list.pop(0)

    def ensure_order(self):
        '''
            Order the sub-command by time. Stable.
        '''
        self.list.sort(key=lambda x: x.time)


class MissingCommandDefinition(Exception):
    pass


class PluginInit1(abc.ABC):
    @abc.abstractmethod
    def run(self, app, *args, **kwargs):
        pass


class PluginInit2(abc.ABC):
    @abc.abstractmethod
    def run(self, app, *args, **kwargs):
        pass


class PluginInit3(abc.ABC):
    @abc.abstractmethod
    def run(self, app, *args, **kwargs):
        pass
