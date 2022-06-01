import re
from typing import Iterable, List, Tuple

from app.bitwork import bit_negate, bit_size, itobl, itoil, uint

ipre = re.compile(r'([0-9A-F]*)\.([0-9A-F]*)\.([0-9A-F]*)\.([0-9A-F]*)')

IP = Tuple[int, int, int, int]


def uip(data: int | List[int] | bytes | str | IP | None) -> IP:
    match data:
        case (int(), int(), int(), int()):
            return tuple([v & 0xFF for v in data])
        case int():
            return ((data & 0xFF000000) >> 24,
                    (data & 0x00FF0000) >> 16,
                    (data & 0x0000FF00) >> 8,
                    (data & 0x000000FF) >> 0)
        case  [*_data] if all(isinstance(i, int) for i in _data):
            _data.reverse()
            val = (0, 0, 0, 0)
            for i, v in enumerate(_data):
                if (i > 3):
                    return val
                val[4-i-1] = v & 0xFF
            return val
        case bytes():
            return uip(list(data))
        case str():
            if (ipre.match(data) is None):
                raise ValueError(f"{data} is not an ip address")
            else:
                return uip([0 if v == '' else int(v) for v in data.split('.')])
        case None:
            return (0, 0, 0, 0)
        case _:
            raise ValueError(
                f"Invalid type passed in argument n({type(data)})")


def iptoi(ip: IP) -> int:
    ip = uip(ip)
    return (ip[0] << 24) |\
        (ip[1] << 16) |\
        (ip[2] << 8) |\
        (ip[3] << 0)


def iptob(ip: IP) -> bytes:
    ip = uip(ip)
    return bytes(list(ip))


def iptostr(ip: IP) -> str:
    return '.'.join(map(str, list(uip(ip))))


def ip_is_mask(ip: IP | int) -> bool:
    if (isinstance(ip, int)):
        return ip >= 0 and ip <= 30
    n = iptoi(uip(ip))
    bl = itobl(n)
    return bit_size(n) == 32 and \
        all(sum(1 for v in bl[:i] if not v) ==
            0 for i, j in enumerate(bl) if j) and \
        sum(1 for v in bl if v) <= 30


def umask(mask: IP | int) -> IP:
    if (isinstance(mask, int)):
        return uip(uint(('1'*mask)+('0'*(32-mask))))
    elif (not ip_is_mask(uip(mask))):
        raise ValueError(
            f"IP mask expected in argument mask, given {iptostr(mask)}")
    else:
        return uip(mask)


def ip_maskton(mask: IP) -> int:
    mask = umask(mask)
    return sum(itoil(iptoi(mask)))


def ip_trivial_mask(ip: IP) -> IP:
    a = list(uip(ip))
    a.reverse()
    pos = next((i for i, v in enumerate(a) if v > 0), 4)
    for i in range(pos, 4):
        a[i] = 255
    a.reverse()
    return umask(a)


def ip_next(ip: IP) -> IP:
    ip = uip(ip)
    if ip == (255, 255, 255, 255):
        return (0, 0, 0, 0)
    else:
        l = list(ip)
        l[3] += 1
        if l[3] >= 255:
            l[3] = 0
            l[2] += 1
            if l[2] >= 255:
                l[2] = 0
                l[1] += 1
                if l[1] >= 255:
                    l[1] = 0
                    l[0] += 1
        return uip(l)


def ip_prev(ip: IP) -> IP:
    ip = uip(ip)
    if ip == (0, 0, 0, 0):
        return (255, 255, 255, 255)
    else:
        l = list(ip)
        l[3] -= 1
        if l[3] <= 0:
            l[3] = 255
            l[2] -= 1
            if l[2] <= 0:
                l[2] = 255
                l[1] -= 1
                if l[1] <= 0:
                    l[1] = 255
                    l[0] -= 1
        return uip(l)


def ip_getnet_ip(ip: IP, mask: IP) -> IP:
    ip = uip(ip)
    mask = umask(mask)

    ip_i = iptoi(ip)
    mask_i = iptoi(mask)

    return uip(mask_i & ip_i)


def ip_getips_innet(ip: IP, mask: IP) -> Iterable[IP]:
    subnet_ip = ip_getnet_ip(ip, mask)

    ip = subnet_ip

    while True:
        yield ip
        ip = ip_next(ip)
        if (ip_getnet_ip(ip, mask) != subnet_ip):
            break


def ip_broadcast_ip(ip: IP, mask: IP) -> IP:
    val: int = iptoi(ip_getnet_ip(ip, mask))
    add: int = bit_negate(iptoi(umask(mask)))
    return uip(val+add)
