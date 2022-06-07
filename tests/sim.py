import json
import logging
import os
from typing import Callable
import unittest
from app.bitwork import byteFormat, itob
from app.core.main import Application, SimContext
from app.mac import IPDataEater
from app.package import get_package_info
from app.ported import PortedElement, isported
from app.port import Port


class SimulationTest(unittest.TestCase):
    def __init__(self, methodName, *args, **kwargs) -> None:
        self.test_name = self.__class__.__name__+"."+methodName
        super().__init__(methodName, *args, **kwargs)

    def init_env(self, wrap_handler: Callable | None = None, check_data_handler: Callable | None = None,
                 missing_directory_ok=False, *args, **kwargs) -> None:
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

        app.check_data_end = self.check_data

        if callable(wrap_handler):
            app.wrap_handler = wrap_handler

        if callable(check_data_handler):
            app.check_data_end = check_data_handler

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
            force=True,
            format='%(levelname)s :: %(message)s'
        )

        os.environ['PYTHONUNBUFFERED'] = '1'

        try:
            app.load_script().run_script_preprocessor().compile_script()
        except FileNotFoundError:
            pass

    def advance(self):
        b = Application.instance.simulation.advance()
        if b is False:
            Application.instance.close_open_files()
        return b

    @staticmethod
    def check_data(e: PortedElement, index: int):
        if not isported(e):
            return
        port = e.get_ports()[index]
        de = port.get_data_eater()
        r = {}
        l1 = {}
        l1['raw'] = de.get_current_data()
        l1['data'] = byteFormat(de.get_current_data(), f'$n:{len(de)}', 'b')
        l1['data_length'] = len(de)
        r['layer_1'] = l1

        if not de.isfinished():
            logging.debug(f"{e.name} recieved a data at {Application.instance.simulation.time}ms in port {port}. Data:\n" +
                          json.dumps(r, ensure_ascii=True, indent=2, sort_keys=True))
            return

        l2 = {}
        l2['origin'] = byteFormat(de.get_origin_mac()[0], f'$n:{4}$')
        l2['target'] = byteFormat(de.get_target_mac()[0], f'$n:{4}$')
        l2['data_size'] = f'{de.get_data_size()[0]} bytes'
        l2['data'] = {
            'raw': de.get_data()[0],
            'bin': {
                'value': byteFormat(de.get_data()[0], f'$n:{de.get_data()[1]}$', 'b'),
                'length': f'{de.get_data()[1]} bits'
            },
            'hex': {
                'value': byteFormat(de.get_data()[0], f'$n:{(de.get_data()[1]+3)//4}$', 'h'),
                'length': f'{(de.get_data()[1]+3)//4} hex characters'
            },
            'bytes': {
                'value': repr(itob(de.get_data()[0], (de.get_data()[1]+7)//8))[1:],
                'length': f'{(de.get_data()[1]+7)//8} bytes'
            }
        }
        l2['corrupt'] = 'yes' if de.iscorrupt() else 'no'
        r['layer_2'] = l2

        try:
            de: IPDataEater = de
            de.ispackage()
        except AttributeError:
            r['type'] = 'frame'
            logging.debug(f"{e.name} recieved a data at {Application.instance.simulation.time}ms in port {port}. Data:\n" +
                          json.dumps(r, ensure_ascii=True, indent=2, sort_keys=True))
            return

        if not de.ispackage():
            r['type'] = 'frame'
            logging.debug(f"{e.name} recieved a data at {Application.instance.simulation.time}ms in port {port}. Data:\n" +
                          json.dumps(r, ensure_ascii=True, indent=2, sort_keys=True))
            return

        l3 = get_package_info(l2["data"]['raw'], de.get_data()[1])
        l3.pop('package')
        l3.pop('total')
        l3["data_length"] = l3["data_length"]
        l3['data'] = {
            'raw': l3['data'],
            'bin': {
                'value': byteFormat(l3['data'], f'$n:{l3["data_length"]}$', 'b'),
                'length': f'{l3["data_length"]} bits'
            },
            'hex': {
                'value': byteFormat(l3['data'], f'$n:{(l3["data_length"]+3)//4}$', 'h'),
                'length': f'{(l3["data_length"]+3)//4} hex characters'
            },
            'bytes': {
                'value': repr(itob(l3['data'], (l3["data_length"]+7)//8))[1:],
                'length': f'{(l3["data_length"]+7)//8} bytes'
            }
        }
        l3.pop("data_length")
        l3['data_size'] = f'{l3["size"]//8} bytes'
        l3.pop("size")
        r['layer_3'] = l3
        r['type'] = 'packet'

        logging.debug(f"{e.name} recieved a data in port {port}. Data:\n" +
                      json.dumps(r, ensure_ascii=True, indent=2, sort_keys=True))


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

        def log_frame():
            de = self.get_ports()[0].get_data_eater()
            storedb = byteFormat(de.get_current_data(),
                                 format=f"$n:{len(de)}$", mode='b')
            storedh = byteFormat(de.get_current_data(),
                                 format=f"$n:{(len(de)+3)//4}$")
            tm = de.get_target_mac()
            tm = byteFormat(tm[0], format=f"n:{tm[1]//4}")
            om = de.get_origin_mac()
            om = byteFormat(om[0], format=f"n:{om[1]//4}")
            datat = de.get_data()
            datat = byteFormat(datat[0], format=f"n:{datat[1]//4}")
            data = ""
            for i in range(0, len(datat), 2):
                if ((i//2) % 64 == 0):
                    data += "\n\t\t"
                data += data[i:i+2]
                data += " "
            logging.info(f"Lector recieved a frame:" +
                         f"\n\ttime:{Application.instance.simulation.time}" +
                         f"\tname:{self.name}" +
                         f"\n\tstored hexadecimal:{storedh}" +
                         f"\n\tstored binary:{storedb}" +
                         f"\nFrame Data:" +
                         f"\n\tTarget Mac: {tm}" +
                         f"\n\tOrigin Max: {om}" +
                         f"\n\tData:{data}")

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
