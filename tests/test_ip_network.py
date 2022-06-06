import logging
from typing import List
from app.core.main import Application, SimElement
from tests.sim import SimulationTest
import app.extensions as sime


class TestIPNetwork(SimulationTest):
    def custom_wrap(self, keyword: str, cmd: str, *params: List[str]):
        if keyword == 'debug':
            logging.debug(f"Executed command:\n" +
                          f"\ttime:{Application.instance.simulation.time}" +
                          f"\tcmd:{cmd}"+f"\tparams:{params}")
        sime.basic_wrap_handler(keyword, cmd, *params)

    def test_twohost(self):
        self.init_env(wrap_handler=self.custom_wrap)

        while self.advance():
            pass

    def test_onerouter_twohost(self):
        self.init_env(wrap_handler=self.custom_wrap)

        while self.advance():
            pass

    def test_clashlands(self):
        self.init_env(wrap_handler=self.custom_wrap)

        while self.advance():
            pass

    def test_ping_pong(self):
        self.init_env(wrap_handler=self.custom_wrap)

        while self.advance():
            pass
