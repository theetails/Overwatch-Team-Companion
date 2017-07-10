from PIL import ImageGrab
import numpy as np
from datetime import datetime
import subprocess as sp
import copy

from Statistics import Statistics
from AllHeroes import AllHeroes
from MapInfo import MapInfo
from TimeInfo import TimeInfo


class Game:
    def __init__(self, debug_mode):
        self.debugMode = debug_mode
        self.heroes = AllHeroes(debug_mode)
        self.map = MapInfo(debug_mode)
        self.gameTime = TimeInfo(debug_mode)
        self.statistics = None
        self.game_over = True

    def main(self, broadcaster):
        sleep_time = None
        current_time = datetime.now()
        current_time_string = datetime.strftime(current_time, "%m-%d-%y %H-%M-%S")

        screen_img_array = self.get_screen()
        current_view = self.map.main(screen_img_array, current_time_string)
        if current_view:
            sp.call('cls', shell=True)
            print(self.map.get_current_map())
            print(current_view)
            if current_view == "Tab":
                sleep_time = 0.5
                self.map.identify_objective_progress(screen_img_array)
                self.gameTime.main(screen_img_array, current_time)
            elif current_view == "Hero Select":
                sleep_time = 1

            # check if map or side changed
            map_changed = self.map.mapChange
            if current_view == "Hero Select":
                side_changed = self.map.identify_side(screen_img_array)
            else:
                side_changed = False

            self.heroes.main(screen_img_array, current_time_string, current_view)

            if map_changed or side_changed:
                self.map.broadcast_options(broadcaster)
                self.map.reset_objective_progress()
                self.game_over = False
            if map_changed and current_view == "Hero Select":
                print("ClearEnemyHeroes")
                self.heroes.clear_enemy_heroes(broadcaster)
                self.statistics = Statistics(self.debugMode)
            else:  # because clear_enemy_heroes already broadcasts heroes
                heroes_changed = self.heroes.check_for_change()
                if heroes_changed:
                    self.heroes.broadcast_heroes(broadcaster)
        else:
            sleep_time = 0.5
            if self.game_over is False:
                self.map.identify_objective_progress(screen_img_array)

        # game stats tracking
        if self.statistics is not None:
            if self.map.objectiveProgress["gameOver"]:
                self.game_over = True
                print("Submit Stats and Clear")
                self.statistics.submit_stats(self.map.objectiveProgress["gameEnd"], current_time_string)
                self.statistics = None
                # TODO remove
                # self.map.reset_objective_progress()
            else:
                self.statistics.add_snapshot(self.heroes.heroesList, self.map.get_current_map(),
                                             self.map.currentMapSide, copy.deepcopy(self.map.get_objective_progress()),
                                             self.gameTime.get_current_game_time(current_time))

        return sleep_time

    @staticmethod
    def get_screen():
        screen_img = ImageGrab.grab(bbox=None)
        return np.asarray(screen_img)
