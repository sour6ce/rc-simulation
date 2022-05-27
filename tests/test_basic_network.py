import logging
from typing import List
from tests.sim import SimulationTest
import app.simulation_extensions as sime
from app.core.main import Application, CommandDef
import app.belements as be


class TestTimer(SimulationTest):
    def custom_wrap(self, keyword: str, cmd: str, *params: List[str]):
        if keyword == 'debug':
            logging.debug(f"Executed command:\n" +
                          f"\ttime:{Application.instance.simulation.time}" +
                          f"\tcmd:{cmd}"+f"\tparams:{params}")
        sime.basic_wrap_handler(keyword, cmd, *params)
        
    def test_karlsendhi(self):
        self.init_env(wrap_handler=self.custom_wrap)
        
        karl=sime.create_element('dispenser','karl')
        federik=sime.create_element('lector','federik')
        
        be.get_port_byname('karl_1').connect(be.get_port_byname('federik_1'))
        
        k=list(be.get_ports_byname('karl_1'))
        
        self.assertEqual(1,len(k))
        
        k=k[0]
        
        k.send_one()
        
        sime.schedule_forced_update(25)
        
        self.advance()
        
        k.end_data()
