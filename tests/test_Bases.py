from random import randint
import unittest
from app.bases import *
from app.bitwork import *


class TestChecksumAl(unittest.TestCase):
    def test1(self):
        a = uint('0x15')
        b = uint(21)

        self.assertEqual(a, b)
        self.assertEqual(chksum(a), chksum(b))

    def test2(self):
        a = uint('FF A9 30 B5')
        b = uint(byteFormat(uint('FF')) +
                 byteFormat(uint(169)) +
                 byteFormat(uint('0011 0000 1011 0101')))

        self.assertEqual(a, b)

        self.assertEqual(chksum(a), chksum(b))

    def test3(self):
        a = [randint(1, 1 << 30) for i in range(100)]
        b = a[100:]
        a = a[:100]

        for i, j in zip(a, b):
            if (i == j):
                self.assertEqual(chksum(i), chksum(j))
            else:
                self.assertNotEqual(chksum(i), chksum(j))
