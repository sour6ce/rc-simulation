from typing import Any, Dict, Tuple
from app.bitwork import bit_chop, bit_mask, bit_size, byteFormat, itob, uint
from app.framing import frame_build
from app.ip import IP, iptoi, uip


def get_layer2_protocol_name_from_data(data: int, data_len: int) -> str | None:
    if (data_len < 32):
        return None
    else:
        data = bit_chop(
            data,
            data_len,
            32,
            32
        )
        return itob(data, 4).decode()


def get_layer2_data_from_protocol_name(protocol: str) -> int:
    return uint(protocol[:4].encode(encoding='ascii'))


def package_build(
    target_mac: int,
    origin_mac: int,
    target_ip: IP,
    origin_ip: IP,
    data: int,
    data_len: int | None,
    ttl: int = 0,
    protocol: int = 0
) -> Tuple[int, int]:
    ipd = get_layer2_data_from_protocol_name('IPPK') << 32
    ipd |= iptoi(uip(target_ip))
    ipd <<= 32
    ipd |= iptoi(uip(origin_ip))
    ipd <<= 8
    ipd |= ttl & (bit_mask(8))
    ipd <<= 8
    ipd |= protocol & (bit_mask(8))
    ipd <<= 8

    data_size = len(byteFormat(data, format="$n:c$", mode='b'))//8 if\
        data_len is None else data_len

    ipd |= data_size & (bit_mask(8))
    ipd <<= data_size*8
    ipd |= data & (bit_mask(data_size*8))

    total_size = 4+4+4+1+1+1+data_size

    return frame_build(target_mac, origin_mac, ipd, total_size)


def isippkg(data: int, data_len: int | None = None) -> bool:
    data_len = data_len if data_len is not None else bit_size(data)
    return get_layer2_protocol_name_from_data(data, data_len) == 'IPPK'


def get_package_info(data: int, data_len: int | None) -> Dict[str, Any] | None:
    if not isippkg(data, data_len):
        return None
    r = {}
    r['package'] = data
    r['total'] = data_len
    data_len -= 32
    data &= bit_mask(data_len)
    r['target'] = uip(bit_chop(
        data,
        data_len,
        32,
        32
    ))
    data_len -= 32
    data &= bit_mask(data_len)
    r['origin'] = uip(bit_chop(
        data,
        data_len,
        32,
        32
    ))
    data_len -= 32
    data &= bit_mask(data_len)
    r['ttl'] = uint(bit_chop(
        data,
        data_len,
        8,
        8
    ))
    data_len -= 8
    data &= bit_mask(data_len)
    r['protocol'] = uint(bit_chop(
        data,
        data_len,
        8,
        8
    ))
    data_len -= 8
    data &= bit_mask(data_len)
    r['size'] = uint(bit_chop(
        data,
        data_len,
        8,
        8
    ))
    data_len -= 8
    data &= bit_mask(data_len)
    r['data'] = data

    return r
