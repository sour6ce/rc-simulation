from random import randint
import unittest
from app.framing import *
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


class TestFrames(unittest.TestCase):
    def test_director(self):
        l = [0, False]

        def inc():
            l[0] += 1

        def end():
            l[1] = True

        director = 0xD193
        cast = 0xCA57

        msg = 'Show me the script'
        data = bytes(msg, 'utf-8')
        datai = uint(data)

        frame, size = frame_build(director, cast, datai)

        frame = byteFormat(frame, format=f"$n:{size}$", mode='b')

        de = DataEater(frame_end_feedback=end, data_insertion_feedback=inc)

        [de.put(True) if v == '1' else de.put(False) for v in frame]

        self.assertEqual(l[0], size)
        self.assertEqual(de.get_origin_mac()[0], cast)
        self.assertEqual(de.get_target_mac()[0], director)
        self.assertTrue(l[1])
        self.assertTrue(de.isfinished())
        self.assertFalse(de.iscorrupt())
        self.assertEqual(msg, itob(de.get_data()[0]).decode('utf-8'))

    def test_hung(self):
        l = [0, False]

        def inc():
            l[0] += 1

        def end():
            l[1] = True

        hung = 0x0001
        chang = 0x0002

        msg = "The message arrives in sadness"
        data = bytes(msg, 'utf-8')

        frame, size = frame_build(hung, chang, data)

        frame = byteFormat(frame, format=f"$n:{size}$", mode='b')

        de = DataEater(frame_end_feedback=end, data_insertion_feedback=inc)

        [de.put(True) if v == '1' else de.put(False) for v in frame]

        de._DataEater__data ^= 1 << 45
        de._DataEater__data ^= 1 << 67
        de._DataEater__data ^= 1 << 56

        self.assertEqual(l[0], size)
        self.assertEqual(de.get_origin_mac()[0], chang)
        self.assertEqual(de.get_target_mac()[0], hung)
        self.assertTrue(l[1])
        self.assertTrue(de.isfinished())
        self.assertTrue(de.iscorrupt())
        self.assertNotEqual(msg, itob(de.get_data()[0]).decode('utf-8'))
