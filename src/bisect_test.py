import unittest

from modules import CrossVersion
from modules import Oracle
from modules import Bisecter
from modules import BisecterBuild

from helper import IOQueue
from collections import deque 


class BisectTester(Bisecter):
    def __init__(self, helper: IOQueue) -> None:
        super().__init__(helper)

        self.func = None

    def start_ref_browser(self, ver: int) -> bool:
        return True

    def stop_ref_browser(self) -> None:
        pass

    def set_version_list(self) -> None:
        pass

    def convert_to_ver(self, index: int) -> int:
        return index

    def convert_to_index(self, ver: int) -> int:
        return ver

    def get_chrome(self, ver: int) -> None:
        pass

    def get_pixel_from_html(self, html_file):
        v = self.func(self.cur_mid)
        return v

def assert_():
      raise RuntimeError('assert')

class fake:
    png_a = 'fake_png_a'
    png_b = 'fake_png_b'
    png_c = 'fake_png_c'
    crash = None

class TestBisecter(unittest.TestCase):

    def test1(self):
        print ('test 1 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 9, None), 'test1', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.png_b
            elif rev == 7: return fake.png_b
            elif rev == 9: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 6')
        self.assertEqual(6, vers[1])

    def test2(self):
        print ('\ntest 2 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 9, None), 'test2', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.crash
            elif rev == 7: return fake.png_b
            elif rev == 9: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 7')
        self.assertEqual(7, vers[1])

    def test3(self):
        print ('\ntest 3 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 9, None), 'test3', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.png_c
            elif rev == 7: return fake.png_b
            elif rev == 9: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 6')
        self.assertEqual(6, vers[1])


    def test4(self):
        print ('\ntest 4 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 6, None), 'test4', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 6')
        self.assertEqual(6, vers[1])

    def test5(self):
        print ('\ntest 5 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 7, None), 'test5', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.png_a
            elif rev == 7: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 7')
        self.assertEqual(7, vers[1])

    def test6(self):
        print ('\ntest 6 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 8, None), 'test6', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.crash
            elif rev == 7: return fake.crash
            elif rev == 8: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 8')
        self.assertEqual(8, vers[1])


    def test7(self):
        print ('\ntest 7 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 9, None), 'test7', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            elif rev == 6: return fake.crash
            elif rev == 7: return fake.crash
            elif rev == 8: return fake.crash
            elif rev == 9: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 9')
        self.assertEqual(9, vers[1])

    def test8(self):
        print ('\ntest 8 starts')
        empty = {}
        ioq = IOQueue(empty)
        ioq.insert_to_queue((5, 9, None), 'test8', (fake.png_a, fake.png_b))

        def getPngByRevisionForTesting(rev):
            if rev == 5: return fake.png_a
            if rev == 6: return fake.crash
            elif rev == 7: return fake.png_c
            elif rev == 8: return fake.png_b
            elif rev == 9: return fake.png_b
            else:
                with self.assertRaises(RuntimeError, msg='your exception message'):
                    assert_()
        
        bi = BisectTester(ioq)
        bi.func = getPngByRevisionForTesting
        bi.start()
        bi.join()
        ioq.move_to_preqs()
        vers = ioq.get_vers()
        ret = ioq.pop_from_queue() 
        print ('vers:', vers) 
        print (vers[1], 'should be 7')
        self.assertEqual(7, vers[1])
