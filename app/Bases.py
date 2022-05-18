from typing import List
from typing_extensions import Self


class SimData():
    __match_args__ = ("data")
    data = []

    def __init__(self, data: str | int | List[bool] | Self | None = None):
        match data:
            case str():
                data = data.replace(' ', '')
                val: int = 0
                try:
                    val = int(data, 2)
                except:
                    try:
                        val = int(data, 16)
                    except:
                        raise ValueError(
                            "data argument should be a string of mostly 1's or 0's" +
                            ", a list of booleans or another SimData")
                data = bin(val)[2:]
                self.data: List[bool] =\
                    [True if c == '1' else False
                        for c in data if c == '0' or c == '1']
            case SimData():
                self.data: List[bool] = data.data.copy()
            case [*_data] if all(isinstance(i, bool) for i in _data):
                self.data: List[bool] = data.copy()
            case None:
                pass
            case int():
                self.__init__(bin(data)[2:])
            case _:
                raise ValueError(
                    "data argument should be a string of mostly 1's or 0's" +
                    ", a list of booleans or another SimData")

    def getData(self) -> List[bool]:
        return self.data

    def __eq__(self, __o: object) -> bool:
        return all((i == j for i, j in zip(self.data, SimData(__o).data)))

    def insert(self, index: int, value: bool) -> None:
        self.data.insert(index, value)

    def __str__(self) -> str:
        return self.tobin()

    def __repr__(self) -> str:
        return repr(list(self.tobin()))

    def __len__(self) -> int:
        return len(self.data)

    def tobin(self, complete_bytes=False) -> str:
        d_len = len(self)
        r = ''.join('1' if v else '0' for v in self.data)
        if (d_len % 8 != 0 and complete_bytes):
            return ''.join([((((d_len//8)+1)*8)-d_len)*'0', r])
        return r

    def tohex(self, complete_bytes=False) -> str:
        d_len = len(self)
        b = int(self.tobin(True), 2)
        r = str.upper(hex(b)[2:])
        if (len(r) % 2 != 0 and complete_bytes):
            return ''.join(['0', r])
        return r

    def __int__(self) -> int:
        return int(self.tobin(), 2)
