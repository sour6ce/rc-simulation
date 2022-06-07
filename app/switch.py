from queue import Queue
from typing import Callable, List
from app.bitwork import itoil
from app.core.main import Application, PluginInit1, SimContext
from app.extensions import create_element
from app.mac import BROADCAST_MAC
from app.ported import PortedElement
from app.framing import DataEater
from app.timer import Timer


class Switch(PortedElement):
    def __init__(self, name: str, sim_context: SimContext,
                 nports: int, *args, **kwargs):
        super().__init__(name, sim_context, nports, *args, **kwargs)

        def get_callback_for_frames(i: List[int]):
            def pure():
                index = i[0]
                self.on_frame(index, self.get_ports()[index].get_data_eater())
            return pure

        self.table = {}
        self.__fqueue = Queue()
        self.__current: List[List[int]] = [[]]*int(nports)

        self.__timers: List[None | Timer] = [None]*int(nports)

        [p.get_data_eater().add_frame_end_callback(get_callback_for_frames([i]))
            for i, p in enumerate(self.get_ports())]

    @classmethod
    def get_element_type_name(cls):
        return 'switch'

    def port_from_mac(self, mac: int) -> int:
        if BROADCAST_MAC == mac or mac not in self.table.keys():
            return -1
        else:
            return self.table[mac]

    def on_frame(self, port: int, de: DataEater) -> None:
        input_index = port
        self.table[de.get_origin_mac()[0]] = input_index

        port = -1
        t = de.get_target_mac()[0]
        port = self.port_from_mac(t)
        frame = (de.get_current_data(), len(de))
        tup = (list(itoil(frame[0], frame[1])), port, input_index)
        self.__fqueue.put(tup)
        self.update_output()
        self.update_send()

    def update_output(self) -> None:
        if not self.__fqueue.empty():
            # frame, port, input = self.__fqueue.queue[0]
            # can_move_frame = (port == -1 and
            #                   all((len(cur) == 0 for i, cur in
            #                       enumerate(self.__current) if i != input))) or \
            #     (len(self.__current[port]) == 0)
            # if Application.instance.config['switch_buffer'] == 'on':
            #     can_move_frame = True
            # if can_move_frame:
            # self.__fqueue.get()
            frame, port, input = self.__fqueue.get()
            for i in range(len(self.__current)):
                if i == port or (port == -1 and i != input):
                    self.__current[i] = self.__current[i]+frame

    def timer_function(self, l) -> Callable:
        def pure():
            index = l[0]
            self.__timers[index] = None
            self.get_ports()[index].end_data()

            self.__current[index] = self.__current[index][1:]
            if len(self.__current[index]) != 0:
                self.__send_wait(index)

        return pure

    def __send_wait(self, index) -> None:
        self.get_ports()[index].send_data(self.__current[index][0] > 0)
        self.__timers[index] = create_element(
            'timer',
            f'switch_{self.name}_{index}_send_timer',
            Application.instance.config['signal_time']
        )
        self.__timers[index].add_time_passed_callback(
            self.timer_function([index]))

    def update_send(self) -> None:
        for i, data in enumerate(self.__current):
            if len(data) != 0:
                if self.__timers[i] is None:
                    self.__send_wait(i)

    def update(self):
        pass


class Init(PluginInit1):
    def run(self, app: Application, *args, **kwargs):

        app.elements['switch'] = Switch
