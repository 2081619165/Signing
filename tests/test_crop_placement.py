"""窗口定位纯坐标回归，不启动原生窗口。"""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from crop.placement import choose_bounds

class PlacementTests(unittest.TestCase):
    def test_center_tracks_main_position(self):
        self.assertEqual(choose_bounds((0,100,960,680),(0,0,2400,1040),(900,650)),(30,115,900,650))
        self.assertEqual(choose_bounds((1200,100,960,680),(0,0,2400,1040),(900,650)),(1230,115,900,650))
        self.assertEqual(choose_bounds((200,0,960,680),(0,0,1600,860),(900,650)),(230,15,900,650))
    def test_negative_monitor_and_small_workarea(self):
        for area,size in [((-1920,0,1920,1040),(900,650)),((0,0,800,560),(900,650)),((1920,0,2560,1400),(1350,975))]:
            x,y,w,h=choose_bounds((area[0]+100,200,1000,700),area,size)
            self.assertGreaterEqual(x,area[0]);self.assertGreaterEqual(y,area[1])
            self.assertLessEqual(x+w,area[0]+area[2]);self.assertLessEqual(y+h,area[1]+area[3])
