import logging
from typing import List, ParamSpecArgs
from app.bitwork import bit_get, byteFormat, uint
from app.framing import frame_build
from tests.sim import SimulationTest
import app.extensions as sime
from app.core.main import Application, CommandDef
import app.ported as be


class TestNet(SimulationTest):
    def custom_wrap(self, keyword: str, cmd: str, *params: List[str]):
        if keyword == 'debug':
            logging.debug(f"Executed command:\n" +
                          f"\ttime:{Application.instance.simulation.time}" +
                          f"\tcmd:{cmd}"+f"\tparams:{params}")
        sime.basic_wrap_handler(keyword, cmd, *params)

    def test_karlsendhi(self):
        self.init_env(wrap_handler=self.custom_wrap)

        karl = sime.create_element('dispenser', 'karl')
        federik = sime.create_element('lector', 'federik')

        be.get_port_byname('karl_1').connect(be.get_port_byname('federik_1'))

        k = list(be.get_ports_byname('karl_1'))

        self.assertEqual(1, len(k))

        k = k[0]

        k.send_one()

        sime.schedule_forced_update(25)

        self.advance()

        k.end_data()

    def test_mirion(self):
        self.init_env(wrap_handler=self.custom_wrap)

        while self.advance():
            pass

    def test_parachute(self):
        self.init_env(wrap_handler=self.custom_wrap)

        while self.advance():
            pass