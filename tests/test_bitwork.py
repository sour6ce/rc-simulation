import unittest
from app.bitwork import *


class TestOperations(unittest.TestCase):
    def test_strworkaround(self):
        self.assertEqual(uint('45')+uint('010')+uint('0x0F'), 62)

    def test_hardcore1(self):
        n = 0
        n = bit_append(n, 45)
        n <<= 8
        n = bit_set(n, -2, 5)
        n = bit_sub(n, 0, -8)
        n -= 5
        self.assertEqual(n, 40)


class TestFormat(unittest.TestCase):
    def test1(self):
        self.assertEqual('0FF', byteFormat(255, format='$n:3$', mode='h'))

    def test2(self):
        self.assertEqual('number is 01100101!',
                         byteFormat(uint('01100101'),
                                    format='number is $n:8$!',
                                    mode='b'))

    def test3(self):
        part1 = byteFormat(10, format='$n:4$', mode='h')
        part2 = byteFormat(258, format='$n:4$', mode='h')
        part3 = byteFormat(1, format='$n:2$', mode='h')
        self.assertEqual('000A010201', part1+part2+part3)
