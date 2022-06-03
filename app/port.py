from typing import Callable, List, Type
from typing_extensions import Self
from app.cable import Cable
from app.core.main import SimElement, Application
from app.framing import DataEater


class Port():
    def __init__(self, id: str, data_eater_type: Type[DataEater] = DataEater) -> None:
        self.__id: str = id
        self.__write_cable: Cable = None
        self.__read_cable: Cable = None
        self.__con_port: Port = None

        self.__de = data_eater_type()

        self.__dsend_cb: List[Callable] = []
        self.__drec_cb: List[Callable] = []
        self.__dsend_f_cb: List[Callable] = []
        self.__drec_f_cb: List[Callable] = []

    def isconnected(self) -> bool:
        return not self.__con_port == None

    def connect(self, port: Self) -> bool:
        self.disconnect()
        port.disconnect()
        wc: Cable = Application.instance.elements["__cable"]()
        rc: Cable = Application.instance.elements["__cable"]()

        self.__write_cable = port.__read_cable = wc

        self.__read_cable = port.__write_cable = rc

        self.__con_port = port
        port.__con_port = self

        return True

    def disconnect(self) -> bool:
        if not self.isconnected():
            return False
        else:
            self.end_data()
            self.__con_port.end_data()
            del(self.__read_cable)
            del(self.__write_cable)

            self.__read_cable =\
                self.__write_cable =\
                self.__con_port.__read_cable =\
                self.__con_port.__write_cable =\
                self.__con_port.__con_port = None

            self.__con_port = None

            return True

    def get_write_cable(self) -> Cable:
        return self.__write_cable

    def get_read_cable(self) -> Cable:
        return self.__read_cable

    def get_connected_port(self) -> Self:
        return self.__con_port

    def __on_data_send_start(self, one: bool) -> None:
        [c(one) for c in self.__dsend_cb if callable(c)]

    def __on_data_send_end(self, one: bool) -> None:
        [c(one) for c in self.__dsend_f_cb if callable(c)]

    def __on_data_recieve_start(self, one: bool) -> None:
        self.__de.put(one)
        [c(one) for c in self.__drec_cb if callable(c)]

    def __on_data_recieve_end(self, one: bool) -> None:
        [c(one) for c in self.__drec_f_cb if callable(c)]

    def add_data_send_started_callback(self, call: Callable) -> None:
        if callable(call):
            self.__dsend_cb.append(call)

    def remove_data_send_started_callback(self, call: Callable) -> None:
        if callable(call):
            self.__dsend_cb.remove(call)

    def add_data_send_finished_callback(self, call: Callable) -> None:
        if callable(call):
            self.__dsend_f_cb.append(call)

    def remove_data_send_finished_callback(self, call: Callable) -> None:
        if callable(call):
            self.__dsend_f_cb.remove(call)

    def add_data_recieve_started_callback(self, call: Callable) -> None:
        if callable(call):
            self.__drec_cb.append(call)

    def remove_data_recieve_started_callback(self, call: Callable) -> None:
        if callable(call):
            self.__drec_cb.remove(call)

    def add_data_recieve_finished_callback(self, call: Callable) -> None:
        if callable(call):
            self.__drec_f_cb.append(call)

    def remove_data_send_finished_callback(self, call: Callable) -> None:
        if callable(call):
            self.__drec_f_cb.remove(call)

    def send_data(self, one: bool) -> bool:
        self.__on_data_send_start(one)
        if self.isconnected():
            self.end_data()
            if one:
                self.__write_cable.write_one()
            else:
                self.__write_cable.write_zero()
            self.__con_port.__on_data_recieve_start(one)
            return True
        else:
            return False

    def send_one(self) -> bool:
        return self.send_data(True)

    def send_zero(self) -> bool:
        return self.send_data(False)

    def receiving(self) -> bool:
        if self.isconnected():
            return self.__read_cable.sending()
        else:
            return False

    def receiving_one(self) -> bool:
        return self.receiving() and self.__read_cable.sending_one()

    def receiving_zero(self) -> bool:
        return self.receiving() and self.__read_cable.sending_zero()

    def sending(self) -> bool:
        if self.isconnected():
            c = self.__write_cable
            return c.sending()
        else:
            return False

    def sending_one(self) -> bool:
        return self.sending() and self.__write_cable.sending_one()

    def sending_zero(self) -> bool:
        return self.sending() and self.__write_cable.sending_zero()

    def end_data(self) -> bool:
        if self.isconnected() and self.sending():
            one = self.get_write_cable().sending_one()
            self.__on_data_send_end(one)
            self.__write_cable.end()
            self.__con_port.__on_data_recieve_end(one)
            return True
        else:
            return False

    def getid(self) -> str:
        return self.__id

    def get_data_eater(self) -> DataEater:
        return self.__de

    def __str__(self) -> str:
        return str(self.__id)
