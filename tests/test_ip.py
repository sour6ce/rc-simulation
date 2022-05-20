import unittest
from app.bitwork import uint
from app.ip import *


class TestIP(unittest.TestCase):
    def test_casting(self):
        ip = uip('192.168.10.5')
        ip2 = uip([192, 168, 10, 5])

        self.assertEqual(ip, ip2)

        a = iptoi(ip)
        b = uip(a)

        self.assertEqual(ip, b)

    def test_masking(self):
        ips_true = [uip('255.192.0.0'),
                    uip('255.255.255.0'),
                    uip('255.255..')]

        ips_false = [uip('255.255.255.255'),
                     uip('192.255.255.0'),
                     uip('8.10.100.4')]

        [self.assertFalse(ip_is_mask(ip)) for ip in ips_false]
        [self.assertTrue(ip_is_mask(ip)) for ip in ips_true]

    def test_horse(self):
        ip_horse = uip('195.40.10.255')

        nextip = ip_next(ip_horse)

        m = ip_trivial_mask(nextip)

        self.assertEqual(iptostr(nextip), '195.40.11.0')
        self.assertEqual(iptostr(m), '255.255.255.0')

        ip_horse = ip_next(nextip)
        ip_fox = uip('195.40.11.8')

        self.assertEqual(ip_getnet_ip(ip_horse, m), ip_getnet_ip(ip_fox, m))

    def test_johnny(self):
        johnny = umask(28)

        self.assertEqual(iptostr(johnny), '255.255.255.240')
        self.assertEqual(ip_maskton(johnny), 28)

    def test_mary(self):
        marynet = umask('255.255.255.224')

        l = list(ip_getips_innet(uip('192.168.10.192'), marynet))

        self.assertEqual(len(l), 32)
        self.assertEqual(iptostr(l[2]), '192.168.10.194')
        self.assertEqual(iptostr(l[-1]), '192.168.10.223')
        self.assertEqual(iptostr(l[-2]), '192.168.10.222')
