import logging
import os
from typing import Callable
import unittest
from app.bitwork import byteFormat
from app.core.main import Application, SimContext
from app.belements import PortedElement
from app.port import Port


class SimulationTest(unittest.TestCase):
    def __init__(self, methodName, *args, **kwargs) -> None:
        self.test_name = self.__class__.__name__+"."+methodName
        super().__init__(methodName, *args, **kwargs)

    def init_env(self, wrap_handler: Callable | None = None, missing_directory_ok=False, *args, **kwargs) -> None:
        self.tests_folder = os.path.dirname(os.path.realpath(__file__))
        self.test_working_folder = os.path.join(
            self.tests_folder, self.test_name)
        if (not os.path.exists(self.test_working_folder)):
            os.makedirs(self.test_working_folder, exist_ok=True)
            if missing_directory_ok == False:
                self.assertTrue(
                    False, "Not working directory for simulation test files (folder created now)")
            logging.warning(f"The test {self.test_name} doesn't had a " +
                            f"working directory " +
                            f"{os.split(self.test_working_folder)[1]} on the " +
                            f"side, it may no work well")
        self.run_folder = os.path.split(self.tests_folder)[0]
        app = Application(self.run_folder)

        os.chdir(self.test_working_folder)

        if ('config' in kwargs.keys()):
            if (os.path.isfile(kwargs['config'])):
                app.config_file = kwargs['config']

        app.scan_plugins().import_plugins().run_init1().run_init2().run_init3()

        app.elements['dispenser'] = Dispenser
        app.elements['lector'] = Lector

        app.load_configuration()

        if callable(wrap_handler):
            app.wrap_handler = wrap_handler

        app.config.update(**kwargs)

        if ('output' in kwargs.keys()):
            if (os.path.isdir(kwargs['output'])):
                app.output_dir = kwargs['output']

        if ('script' in kwargs.keys()):
            if (os.path.isfile(kwargs['script'])):
                app.script_file = kwargs['script']

        os.makedirs(app.output_dir, exist_ok=True)

        f = open(os.path.join(app.output_dir, 'out.log'), 'a')
        f.close()

        logging.basicConfig(
            filename=os.path.join(app.output_dir, 'out.log'),
            level=logging.DEBUG,
            filemode='w',
            force=True
        )

        try:
            app.load_script().run_script_preprocessor().compile_script()
        except FileNotFoundError:
            pass

    def advance(self):
        return Application.instance.simulation.advance()


class Dispenser(PortedElement):
    def __init__(self, name: str, sim_context: SimContext, *args, **kwargs):
        super().__init__(name, sim_context, 1, *args, **kwargs)

        def log_sending(one: bool):
            logging.info(f"Dispenser start sending a bit:" +
                         f"\ttime:{Application.instance.simulation.time}" +
                         f"\tname:{self.name}" +
                         f"\n\tvalue: {'1' if one else '0'}")

        def log_finished(one: bool):
            logging.info(f"Dispenser end sending a bit:" +
                         f"\ttime:{Application.instance.simulation.time}" +
                         f"\tname:{self.name}" +
                         f"\n\tvalue: {'1' if one else '0'}")

        self.get_ports()[0].add_data_send_started_callback(log_sending)
        self.get_ports()[0].add_data_send_finished_callback(log_finished)

    def update(self):
        logging.info(f"Dispenser on update:" +
                     f"\ttime:{Application.instance.simulation.time}" +
                     f"\tname:{self.name}")

    @classmethod
    def get_element_type_name(cls):
        return 'dispenser'


class Lector(PortedElement):
    def __init__(self, name: str, sim_context: SimContext, *args, **kwargs):
        super().__init__(name, sim_context, 1, *args, **kwargs)

        def log_recieve(one: bool):
            de = self.get_ports()[0].get_data_eater()
            storedb = byteFormat(de.get_current_data(),
                                 format=f"$n:{len(de)}$", mode='b')
            storedh = byteFormat(de.get_current_data(),
                                 format=f"$n:{(len(de)+3)//4}$")
            logging.info(f"Lector start recieving a bit:" +
                         f"\ttime:{Application.instance.simulation.time}" +
                         f"\tname:{self.name}" +
                         f"\n\tvalue: {'1' if one else '0'}" +
                         f"\nNew Stored Values:" +
                         f"\n\tstored hexadecimal:{storedh}" +
                         f"\n\tstored binary:{storedb}")

        def log_finished(one: bool):
            logging.info(f"Lector end recieving a bit:" +
                         f"\ttime:{Application.instance.simulation.time}" +
                         f"\tname:{self.name}" +
                         f"\n\tvalue: {'1' if one else '0'}")

        self.get_ports()[0].add_data_recieve_started_callback(log_recieve)
        self.get_ports()[0].add_data_recieve_finished_callback(log_finished)

    def update(self):
        de = self.get_ports()[0].get_data_eater()
        storedb = byteFormat(de.get_current_data(),
                             format=f"$n:{len(de)}$", mode='b')
        storedh = byteFormat(de.get_current_data(),
                             format=f"$n:{(len(de)+3)//4}$")
        logging.info(f"Lector on update:" +
                     f"\ttime:{Application.instance.simulation.time}" +
                     f"\tname:{self.name}" +
                     f"\n\tstored hexadecimal:{storedh}" +
                     f"\n\tstored binary:{storedb}")

    @classmethod
    def get_element_type_name(cls):
        return 'lector'

    def send(self, port: Port | int, one: bool) -> bool:
        raise Exception("Why would you use a Lector to send information?")
