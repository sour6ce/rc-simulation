import unittest
from app.arp import build_arpq, build_arpr, isdataARPQ, isdataARPR, getARPIP, ARP_FRAME_SIZE
from app.bitwork import itobl
from app.framing import DataEater
from app.ip import uip


class TestARP(unittest.TestCase):
    def test_protect(self):
        ip = '192.168.5.40'
        my_arpq = build_arpq(0x5600, ip)

        arpq_de = DataEater()

        [arpq_de.put(v) for v in itobl(my_arpq[0], ARP_FRAME_SIZE*8)]

        self.assertIs(arpq_de.isfinished(), True)
        self.assertIs(isdataARPQ(arpq_de.get_data()[0]), True)
        self.assertIs(isdataARPR(arpq_de.get_data()[0]), False)

        ip_getted = getARPIP(arpq_de.get_data()[0])
        self.assertEqual(ip_getted, uip(ip))

        my_arpr = build_arpr(0xA0A1, 0x5600, ip_getted)

        arpr_de = DataEater()

        [arpr_de.put(v) for v in itobl(my_arpr[0], ARP_FRAME_SIZE*8)]

        self.assertIs(arpr_de.isfinished(), True)
        self.assertIs(isdataARPQ(arpr_de.get_data()[0]), False)
        self.assertIs(isdataARPR(arpr_de.get_data()[0]), True)

        ip_getted = getARPIP(arpr_de.get_data()[0])
        self.assertEqual(ip_getted, uip(ip))
