from typing import Callable, List, Tuple
from typing_extensions import Self

from app.bitwork import bit_append, bit_chop, bit_mask, bit_sub, byteFormat, uint


def chksum(data: int) -> int:
    data = byteFormat(data, format='$n:c$')
    d_len = len(data)

    # Separate each byte and turn it into int
    data = [int(data[i:i+2], 16) if i + 1 < d_len else int(data[i:], 16)
            for i in range(0, d_len, 2)]

    d_len = (d_len+1)//2
    sum = 0

    # make 16 bit words out of every two adjacent 8 bit words in the packet
    # and add them up
    for i in range(0, d_len, 2):
        if i + 1 >= d_len:
            sum += (data[i]) & 0xFF
        else:
            w = (((data[i]) << 8) & 0xFF00) + ((data[i+1]) & 0xFF)
            sum += w

    # take only 16 bits out of the 32 bit sum and add up the carries
    while (sum >> 16) > 0:
        sum = (sum & 0xFFFF) + (sum >> 16)

    # one's complement the result
    sum = ~sum

    return sum & 0xFFFF


MAC_BYTESIZE = 2
DATASIZE_BYTESIZE = 1
VALIDATIONSIZE_BYTESIZE = 1
VALIDATION_BYTESIZE = 2
MACSECTION_BYTESIZE = MAC_BYTESIZE*2
HEADER_BYTESIZE = MACSECTION_BYTESIZE+DATASIZE_BYTESIZE +\
    VALIDATIONSIZE_BYTESIZE


class DataEater():
    __data = 0
    __data_size = 0

    def __init__(self, frame_end_feedback: Callable | None = None,
                 data_insertion_feedback: Callable | None = None,):
        self.__fef: List[Callable] = [frame_end_feedback] \
            if frame_end_feedback != None else []
        self.__dif: List[Callable] = [data_insertion_feedback] \
            if data_insertion_feedback != None else []

        self.clear()

    def get_current_data(self) -> int:
        return self.__data

    def __len__(self) -> int:
        return self.__data_size

    def isfinished(self) -> bool:
        self.try_calc_tsize()
        return self.__finished

    def get_header(self) -> Tuple[int, int] | None:
        if len(self)//8 >= HEADER_BYTESIZE:
            return (bit_chop(self.__data, len(self),
                             HEADER_BYTESIZE*8,
                             HEADER_BYTESIZE*8), HEADER_BYTESIZE*8)
        else:
            return None

    def get_target_mac(self) -> Tuple[int, int] | None:
        if len(self)//8 >= MAC_BYTESIZE:
            return (bit_chop(self.__data, len(self),
                             MAC_BYTESIZE*8,
                             MAC_BYTESIZE*8), MAC_BYTESIZE*8)
        else:
            return None

    def get_origin_mac(self) -> Tuple[int, int] | None:
        if len(self)//8 >= MACSECTION_BYTESIZE:
            return (bit_chop(self.__data, len(self),
                             MAC_BYTESIZE*8,
                             MACSECTION_BYTESIZE*8), MAC_BYTESIZE*8)
        else:
            return None

    def get_data_size(self) -> Tuple[int, int] | None:
        if len(self)//8 >= MACSECTION_BYTESIZE+DATASIZE_BYTESIZE:
            return (bit_chop(self.__data, len(self),
                             DATASIZE_BYTESIZE*8,
                             MACSECTION_BYTESIZE*8+DATASIZE_BYTESIZE*8), DATASIZE_BYTESIZE*8)
        else:
            return None

    def get_validation_size(self) -> Tuple[int, int] | None:
        return (VALIDATION_BYTESIZE, VALIDATIONSIZE_BYTESIZE*8)

    def get_data(self) -> Tuple[int, int] | None:
        data_size = self.get_data_size()
        if data_size is None:
            return None
        data_size = data_size[0]*8
        if len(self) >= HEADER_BYTESIZE*8 + data_size:
            return (bit_chop(self.__data, len(self),
                             data_size,
                             HEADER_BYTESIZE*8+data_size), data_size)
        else:
            return None

    def get_validation(self) -> Tuple[int, int] | None:
        data_size = self.get_data_size()
        validation_size = self.get_validation_size()
        if (data_size is None) or (validation_size is None):
            return None
        data_size = data_size[0]*8
        validation_size = validation_size[0]*8
        if self.__finished:
            return (bit_chop(self.__data, len(self),
                             validation_size,
                             len(self)), validation_size)
        else:
            return None

    def iscorrupt(self) -> bool:
        data = self.get_data()
        validation = self.get_validation()
        if validation is None or data is None:
            return False
        else:
            data = data[0]
            validation = validation[0]
            return chksum(data) != validation

    def clear(self) -> None:
        self.__finished = False
        self.__data = 0
        self.__data_size = 0
        self.__expected_size = -1

    def put(self, one: bool) -> None:
        if self.isfinished():
            self.clear()

        self.__data = bit_append(self.__data, uint([one]))

        self.__data_size += 1

        self.try_calc_tsize()

        [call() for call in self.__dif]
        if self.isfinished():
            [call() for call in self.__fef]

    def try_calc_tsize(self):
        if self.__expected_size == -1:
            data_size = self.get_data_size()
            val_size = self.get_validation_size()
            if data_size is not None and val_size is not None:
                data_size = data_size[0]*8
                val_size = val_size[0]*8
                self.__expected_size = HEADER_BYTESIZE*8+data_size +\
                    val_size
            else:
                self.__expected_size = -1
        else:
            if len(self) == self.__expected_size:
                self.__finished = True

    def add_data_insertion_callback(self, call: Callable) -> None:
        self.__dif.append(call)

    def remove_data_insertion_callback(self, call: Callable) -> None:
        self.__dif.remove(call)

    def add_frame_end_callback(self, call: Callable) -> None:
        self.__fef.append(call)

    def remove_frame_end_callback(self, call: Callable) -> None:
        self.__fef.remove(call)


def frame_build(target_mac: int, origin_mac: int,  data: int) -> Tuple[int, int]:
    origin_mac = uint(origin_mac)
    target_mac = uint(target_mac)
    data = uint(data)

    r = 0
    r |= target_mac & bit_mask(MAC_BYTESIZE*8)
    r <<= (MAC_BYTESIZE*8)
    r |= origin_mac & bit_mask(MAC_BYTESIZE*8)
    r <<= (DATASIZE_BYTESIZE*8)

    data_size = len(byteFormat(data, format="$n:c$", mode='b'))//8

    r |= data_size & bit_mask(DATASIZE_BYTESIZE*8)
    r <<= (VALIDATIONSIZE_BYTESIZE*8)
    r |= VALIDATION_BYTESIZE & bit_mask(VALIDATIONSIZE_BYTESIZE*8)
    r <<= (data_size*8)
    r |= data & bit_mask(data_size*8)
    r <<= (VALIDATION_BYTESIZE*8)
    r |= chksum(data) & bit_mask(VALIDATION_BYTESIZE*8)

    return (r, HEADER_BYTESIZE*8+data_size*8+VALIDATION_BYTESIZE*8)
