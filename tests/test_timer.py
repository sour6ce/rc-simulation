import logging
from sqlite3 import Time
from typing import List
from tests.sim import SimulationTest
import app.extensions as sime
from app.core.main import Application, CommandDef
from app.timer import Timer


class TestTimer(SimulationTest):
    def custom_wrap(self, keyword: str, cmd: str, *params: List[str]):
        if keyword == 'debug':
            logging.debug(f"Executed command:\n" +
                          f"\ttime:{Application.instance.simulation.time}" +
                          f"\tcmd:{cmd}"+f"\tparams:{params}")
        sime.basic_wrap_handler(keyword, cmd, *params)

    def test_switches_watches(self):
        self.init_env(wrap_handler=self.custom_wrap)

        blank_cmd: CommandDef = Application.instance.pv_commands['blank']

        blank_cmd.run = lambda *params: logging.debug(
            f"Executed update at "+str(Application.instance.simulation.time))

        timer: Timer = sime.create_element('timer', 'alt', 50)
        timer.add_time_passed_callback(
            lambda: logging.info("Callback on timer alt executed"))

        while self.advance():
            pass

        items = [e.name for e in sime.get_elements_bytype(Timer)]
        items_by_name = [
            sime.get_element_byname("alt").name,
            sime.get_element_byname("t1").name,
            sime.get_element_byname("t2").name,
            sime.get_element_byname("t3").name
        ]
        self.assertListEqual(items, items_by_name)
        self.assertListEqual(items, ['alt', 't1', 't2', 't3'])
        
        sime.schedule_command(20,"$",'debug','print','all_well')
        
        while self.advance():
            pass
