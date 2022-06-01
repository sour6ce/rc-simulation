import unittest
from app.bitwork import itobl, itoil
from app.framing import DataEater
from app.ip import iptostr
from app.package import package_build, get_package_info


class TestIP(unittest.TestCase):
    def test_mankind(self):
        frame=package_build(
            0x0A0A,
            0x0001,
            '192.168.67.30',
            '192.168.65.23',
            0x12345678,
            4
        )
        
        de=DataEater()
        
        frame=itobl(frame[0],frame[1])
        [de.put(b) for b in frame]
        
        self.assertIs(de.isfinished(),True)
        
        d=de.get_data()
        pkg=get_package_info(d[0],d[1])
        
        self.assertEqual(iptostr(pkg['target']),'192.168.67.30')
        self.assertEqual(iptostr(pkg['origin']),'192.168.65.23')
        self.assertEqual(pkg['data'],0x12345678)
        