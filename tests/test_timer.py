import logging
from typing import List
from tests.sim import SimulationTest
import app.simulation_extensions as sime
from app.core.main import Application, CommandDef


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

        while self.advance():
            pass
        
