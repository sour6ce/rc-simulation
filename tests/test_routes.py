import unittest
from app.ip import uip
from app.routes import RouteTable, RouteTableInstance, cast_route


class TestRoutes(unittest.TestCase):
    def test_tauron(self):
        rt = RouteTable(False)

        r1 = cast_route('192.168.10.0', '255.255.255.0', '0.0.0.0', 1)
        r2 = cast_route('192.168.0.0', '255.255.0.0', '192.168.0.1', 2)
        r3 = cast_route('192.134.12.0', '255.255.255.0', '192.168.0.1', 2)

        rt.add(*r1)
        rt.add(*r2)
        rt.add(*r3)

        t1 = uip('192.168.10.5')
        t2 = uip('192.168.34.90')
        t3 = uip('192.134.12.180')
        t4 = uip('167.12.3.4')

        self.assertEqual(rt.get_match(t1), r1)
        self.assertEqual(rt.get_match(t2), r2)
        self.assertEqual(rt.get_match(t3), r3)
        self.assertIsNone(rt.get_match(t4))

        rt.remove(*r3)

        self.assertIsNone(rt.get_match(t3))
