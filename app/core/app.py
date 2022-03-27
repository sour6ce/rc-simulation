import os
import importlib
import inspect
import types
from fnmatch import fnmatch
import app.core.script as script
import app.core.plugins as plugins
import app.core.simulation as sim

class Application:
    def __init__(self, app_path):
        self.app_path=app_path #Main directory of the app
        self.plugins_files=[] #Filenames of all plugins
        self.plugins=[] #Module Python objects of the loaded plugins
        self.first_inits=[] #Initialization classes for the first stage
        self.second_inits=[] #Initialization classes for the second stage
        self.third_inits=[] #Initialization classes for the third stage
        self.commands={} #Avaiable commands in the app
        self.pv_commands={} #Avaiable private commands in the app
        self.elements={} #Avaiable network elements in the app
        self.script_pipe=[] #Script pre-processors loaded
        self.pre_command_hooks=[] #Hooks to execute before commands loaded
        self.post_command_hooks=[] #Hooks to execute after commands loaded
        self.global_updates_hooks=[] #Hooks to execute on update

        self.script_file="script.txt" #The filename of the script to execute
        self.script=[] #Each line of the script

        self.config={} #Stores configuration values of the app
        self.config_file="config.txt" #File that will override the configuration setted by plugins

        self.output_dir=os.path.join(app_path,"output") #Directory where element output should go

        self.simulation=sim.SimContext(self) #Current simulation information

    def resolve_command(self,cmd_name):
        '''
            Finds the command with the given name, public or private. Used to easy the sub-command creation. Prioritize public.
            Returns False if command is not found.
        '''
        if cmd_name in self.commands.keys() and isinstance(self.commands[cmd_name],script.CommandDef):
            return self.commands[cmd_name]
        if cmd_name in self.pv_commands.keys() and isinstance(self.pv_commands[cmd_name],script.CommandDef):
            return self.pv_commands[cmd_name]
        return False

    def scan_plugins(self):
        '''
            Get the scripts filenames from the files in app directory.
        '''
        self.plugins_files=[py for py in os.listdir(os.path.join(self.app_path,"app")) if os.path.isfile(os.path.join(os.path.join(self.app_path,"app"),py)) and fnmatch(py,"*.py")]
        return self

    def import_plugins(self):
        '''
            Load the objects defined in app folder.
        '''
        self.plugins=[importlib.import_module("app."+os.path.splitext(f)[0]) for f in self.plugins_files] #TODO: Log errors at loading plugins
        
        #Order plugins according to the load order defined in them. If it's not defined is assumed that is zero.
        def plugin_lo(p):
            next((c for n,c in inspect.getmembers(p) if (n=='LOAD_ORDER')),0)

        self.plugins.sort(key=plugin_lo)

        #Get initialization classes for each stage
        self.first_inits=[c for plugin in self.plugins for n,c in inspect.getmembers(plugin) if inspect.isclass(c) and issubclass(c,plugins.PluginInit1)]
        self.second_inits=[c for plugin in self.plugins for n,c in inspect.getmembers(plugin) if inspect.isclass(c) and issubclass(c,plugins.PluginInit2)]
        self.third_inits=[c for plugin in self.plugins for n,c in inspect.getmembers(plugin) if inspect.isclass(c) and issubclass(c,plugins.PluginInit3)]
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
        f=open(self.script_file,'r')
        self.script=f.readlines()
        f.close()
        return self

    def run_script_preprocessor(self):
        '''
            Execute every callable preprocessor of script registered by the app.
        '''
        for spp in self.script_pipe:
            if callable(spp):
                self.script=spp(self.script)
        return self            

    def compile_script(self):
        '''
            Analyze the script lines and push the commands in the queue to execute.
        '''
        for l in self.script:
            c=l.split(' ')
            time=int(c[0])
            cmd_name=c[1]
            args=[]
            if len(c)>2:
                args=c[2:]

            if cmd_name not in self.commands.keys() or not isinstance(self.commands[cmd_name],script.CommandDef):
                raise(script.MissingCommandDefinition(f"{cmd_name} command definition not founded among public commands."))
            else:
                self.simulation.p_queue.add_late(script.SubCommand(time,self.commands[cmd_name],*args))


    def load_configuration(self):
        '''
            Load the config from the config file. Overrides current stored configuration values.
        '''
        f=open(self.config_file,'r')
        lines=f.readlines()
        f.close()

        for l in lines:
            if l.strip() and l.count('=')==1:
                eq_pos=l.find('=')
                self.config[l[:eq_pos].replace(' ','_')]=l[eq_pos+1:]
        return self()
                