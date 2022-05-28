from app.bitwork import byteFormat
from app.framing import MAC_BYTESIZE

BROADCAST_MAC = (1 << (8*MAC_BYTESIZE))-1
BROADCAST_MAC_STR = byteFormat(BROADCAST_MAC, f"$n:{MAC_BYTESIZE*2}")


def is_for_me(my_mac: int, target_mac: int) -> bool:
    return my_mac == target_mac or target_mac == BROADCAST_MAC
