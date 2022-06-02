from typing import Tuple
from app.bitwork import bit_append, bit_chop
from app.ip import IP, iptoi, uip
from app.framing import HEADER_BYTESIZE, VALIDATION_BYTESIZE, frame_build
from app.mac import BROADCAST_MAC
from app.package import get_layer2_data_from_protocol_name, get_layer2_protocol_name_from_data

ARP_FRAME_SIZE = HEADER_BYTESIZE+VALIDATION_BYTESIZE+8


def build_arpq(origin_mac: int, ip: IP) -> Tuple[int, int]:
    data = get_layer2_data_from_protocol_name('ARPQ')
    data = bit_append(data, iptoi(uip(ip)), 32)
    return (frame_build(BROADCAST_MAC, origin_mac, data, 8)[0], ARP_FRAME_SIZE)


def build_arpr(origin_mac: int, target_mac: int, ip: IP) -> Tuple[int, int]:
    data = get_layer2_data_from_protocol_name('ARPR')
    data = bit_append(data, iptoi(uip(ip)), 32)
    return (frame_build(target_mac, origin_mac, data, 8)[0], ARP_FRAME_SIZE)


def isdataARPQ(data: int, data_len: int = 64) -> bool:
    return get_layer2_protocol_name_from_data(data, data_len) == 'ARPQ'


def isdataARPR(data: int, data_len: int = 64) -> bool:
    return get_layer2_protocol_name_from_data(data, data_len) == 'ARPR'


def getARPIP(data: int, data_len: int = 64) -> IP:
    return uip(bit_chop(data, data_len, 32, 64))
