from PIL import ImageGrab
import numpy as np
import time
import subprocess as sp

from AllHeroes import AllHeroes
from MapInfo import MapInfo
from TimeInfo import TimeInfo


class Game:
    def __init__(self, debug_mode):
        self.debugMode = debug_mode
        self.heroes = AllHeroes(debug_mode)
        self.map = MapInfo(debug_mode)
        self.gameTime = TimeInfo(debug_mode)

    def main(self, broadcaster):
        sleep_time = None

        screen_img_array = self.get_screen()
        current_time = str(int(time.time()))
        current_view = self.map.main(screen_img_array)
        if current_view:
            sp.call('cls', shell=True)
            print(self.map.currentMap[0])
            print(current_view)
            if current_view == "Tab":
                sleep_time = 0.5
                self.map.identify_objective_progress(screen_img_array)
                self.gameTime.main(screen_img_array)
            elif current_view == "Hero Select":
                sleep_time = 1
            self.heroes.main(screen_img_array, current_time, current_view)

            map_changed = self.map.mapChange
            if current_view == "Hero Select":
                side_changed = self.map.identify_side(screen_img_array)
            else:
                side_changed = False
            if (self.map.thisMapPotential < self.map.imageThreshold[current_view]) and self.debugMode:
                self.map.save_debug_data(current_time)
            if map_changed or side_changed:
                self.map.broadcast_options(broadcaster)
                self.map.reset_objective_progress()
            if map_changed and current_view == "Hero Select":
                print("ClearEnemyHeroes")
                self.heroes.clear_enemy_heroes(broadcaster)
            elif side_changed:
                heroes_changed = self.heroes.check_for_change()
                if heroes_changed:
                    self.heroes.broadcast_heroes(broadcaster)
            else:
                heroes_changed = self.heroes.check_for_change()
                if heroes_changed:
                    self.heroes.broadcast_heroes(broadcaster)
        else:
            sleep_time = 0.5
            heroes_changed = self.heroes.check_for_change()
            if heroes_changed:
                self.heroes.broadcast_heroes(broadcaster)

            # Check for Objective Progress Here
            self.map.identify_objective_progress(screen_img_array)

        return sleep_time

    @staticmethod
    def get_screen():
        screen_img = ImageGrab.grab(bbox=None)
        return np.asarray(screen_img)
