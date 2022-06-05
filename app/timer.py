from typing import Callable, List
from app.core.main import Application
import app.core.main as sim
import app.core.main as main
from app.extensions import schedule_forced_update, delete_element


class Timer(sim.SimElement):
    def __init__(self, name: str, sim_context: sim.SimContext, time: int, *args, **kwargs):
        self.curent_time = int(time)
        self.initial_time = int(time)
        self.initial_total_time: int = sim_context.time
        self.finished: bool = False
        self.__cb: List[Callable] = []
        schedule_forced_update(self.initial_time)
        super().__init__(name, sim_context, time, *args, **kwargs)

    @classmethod
    def get_element_type_name(cls):
        return 'timer'

    def update(self):
        ctime = Application.instance.simulation.time
        self.curent_time = self.initial_time-(ctime-self.initial_total_time)
        if self.curent_time == 0:
            [c() for c in self.__cb if callable(c)]
            self.finished = True
            delete_element(self.name)
            return

    def add_time_passed_callback(self, call: Callable) -> None:
        self.__cb.append(call)

    def remove_time_passed_callback(self, call: Callable) -> None:
        self.__cb.remove(call)


class TimerInit(main.PluginInit1):
    def run(self, app: Application, *args, **kwargs):
        app.elements['timer'] = Timer
