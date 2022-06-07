import logging
from sys import stdout
import fire
import importlib
import os
from app.core.main import Application

def run_app(*args,**kwargs):
    logging.basicConfig(stream=stdout,level=logging.INFO,force=True)
    
    app=Application(os.path.dirname(os.path.realpath(__file__)))
            
    if ('config' in kwargs.keys()):
        if (os.path.isfile(kwargs['config'])):
            app.config_file=kwargs['config']
      
    app.scan_plugins().import_plugins().run_init1().run_init2().run_init3()          
    app.load_configuration()
    
    app.config.update(**kwargs)
    
    if ('output' in kwargs.keys()):
        if (os.path.isdir(kwargs['output'])):
            app.output_dir=kwargs['output']
            
    if ('script' in kwargs.keys()):
        if (os.path.isfile(kwargs['script'])):
            app.script_file=kwargs['script']
            
    app.load_script().run_script_preprocessor().compile_script()

    while app.simulation.advance():
        pass
    
    Application.instance.close_open_files()

if __name__ == '__main__':
    fire.Fire(run_app)