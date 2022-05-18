import unittest
from app.Bases import *


class TestData(unittest.TestCase):
    def test_repr(self):
        a = SimData()
        a.data = [True, True, False, True]
        self.assertEqual(repr(a), repr(['1', '1', '0', '1']))

    def test_str(self):
        a = SimData()
        a.data = [True, True, False, True]
        self.assertEqual(str(a), '1101')

    def test_tobin_cb(self):
        a = SimData()
        a.data = [True, True, True, False, True]
        self.assertEqual(a.tobin(True), '00011101')

    def test_hexform_coff(self):
        a = SimData()
        a.data = [True, True, True, False, True]
        self.assertEqual(a.tohex(), '1D')

    def test_hexform_con(self):
        a = SimData()
        a.data = [True, True, False, True]
        self.assertEqual(a.tohex(True), '0D')

    def test_ctor_vs_hex(self):
        a = SimData('1111 0111 1001 1010 0000')
        self.assertEqual(a.tohex(True), '0F79A0')

    def test_ctor_bl(self):
        a = SimData([True, False, False, False, True])
        self.assertEqual(a.tobin(True), '00010001')

    def test_ctor_copy(self):
        a = SimData('FF 00')
        b = SimData(a)

        b.insert(0, True)

        self.assertNotEqual(a.tohex(True), b.tohex(True))

    def test_ctor_int(self):
        a = SimData(40)

        self.assertEqual(a.tohex(), '28')

    def test_int_workflow(self):
        a = SimData(56)
        b = SimData(14)
        c = SimData(int(a)-int(b))

        self.assertEqual(int(c), 42)
