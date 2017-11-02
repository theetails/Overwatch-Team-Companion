from PIL import Image
import numpy as np
from datetime import datetime, timedelta

from GameObject import GameObject


class TimeInfo(GameObject):
    def __init__(self, game_version, debug_mode):
        self.game_version = game_version
        self.debug_mode = debug_mode

        self.digitReferences = self.read_references("Reference\\DigitImageList.txt")
        self.colonReference = self.read_references("Reference\\ColonImageList.txt")
        self.digitDimensions = {
            "start_x": 106,
            "end_x": 114,
            "start_y": 59,
            "end_y": 71
        }
        self.game_datetime = datetime.min
        self.roundStartTime = None
        self.newly_verified_game_time = False

    def reset_time(self):
        self.game_datetime = datetime.min
        self.roundStartTime = None

    def main(self, screen_image_array, computer_time_string):
        self.identify_time(screen_image_array, computer_time_string)
        return True

    def identify_time(self, img_array, system_time):
        colon_found = False
        digits_before_colon = 0
        digits_after_colon = 0

        # digit_requirement = 79  # Don't need? If its not a colon, it must be a digit
        colon_requirement = 30

        dimensions = self.digitDimensions.copy()
        loop_count = 0
        time_string = ""
        while True:
            # print("Loop Count: " + str(loop_count))
            if digits_before_colon > 0 and colon_found is False:
                colon_dimensions = dimensions.copy()
                colon_dimensions["end_x"] = colon_dimensions["end_x"] - 5
                this_digit_array = self.cut_and_threshold(img_array, colon_dimensions)
                potential = self.what_image_is_this(this_digit_array, self.colonReference)
                # print("Colon?")
                # print(potential)
                this_colon = max(potential.keys(), key=(lambda k: potential[k]))
                if potential[this_colon] > colon_requirement:
                    # print("Colon!")
                    time_string = time_string + ":"
                    colon_found = True
                    dimensions["start_x"] = dimensions["start_x"] + 4
                    dimensions["end_x"] = dimensions["end_x"] + 4
                    if self.debug_mode:
                        self.save_debug_data(this_digit_array, loop_count, system_time)
                    loop_count = loop_count + 1
                    continue
                # print("Not Colon")

            # TODO have a potential / check for a color | voice chat notifications cover time
            this_digit_array = self.cut_and_threshold(img_array, dimensions)
            potential = self.what_image_is_this(this_digit_array, self.digitReferences)
            this_digit_full = max(potential.keys(), key=(lambda k: potential[k]))
            this_digit_split = this_digit_full.split("-")
            this_digit = this_digit_split[0]

            # these digits are very similar, checking unique pixels to each number
            if this_digit == "3" or this_digit == "6" or this_digit == "8":
                if this_digit_array[6][2][0] == 0:
                    this_digit = "3"
                elif this_digit_array[4][6][0] == 0:
                    this_digit = "6"
                else:
                    this_digit = "8"

            # print(this_digit)
            # print(potential)
            time_string = time_string + str(this_digit)

            if colon_found:
                digits_after_colon = digits_after_colon + 1
            else:
                digits_before_colon = digits_before_colon + 1
            if self.debug_mode:
                self.save_debug_data(this_digit_array, loop_count, system_time)
            if digits_after_colon == 2:
                break
            dimensions["start_x"] = dimensions["start_x"] + 9
            dimensions["end_x"] = dimensions["end_x"] + 9
            if loop_count > 4:
                break
            else:
                loop_count = loop_count + 1
        if time_string[1] == ":" or time_string[2] == ":":  # assume correct read
            try:
                this_time_formatted = datetime.strptime(time_string, "%M:%S")
            except ValueError:
                print("Time Not Right")
            self.game_datetime = this_time_formatted
            print("Game Time: " + datetime.strftime(this_time_formatted, "%M:%S"))
            self.newly_verified_game_time = True

            # self.correct_round_start_time(system_time, time_string)

        else:
            print("Time not reading correctly")
            # TODO save time debug

    # TODO remove function? (in Statistics)
    def correct_round_start_time(self, system_time, game_time_string):
        game_time_string_split = game_time_string.split(":")
        game_time_seconds = int(game_time_string_split[1])
        game_time_minutes = int(game_time_string_split[0])
        game_time_delta = timedelta(minutes=game_time_minutes, seconds=game_time_seconds)

        calculated_start_time = system_time - game_time_delta

        # initial time
        if self.roundStartTime is None:  # and time > 0:00
            print("Round Start Time: " + datetime.strftime(calculated_start_time, "%H:%M:%S"))
            self.roundStartTime = calculated_start_time

        seconds_difference = (calculated_start_time - self.roundStartTime).total_seconds()
        # print(seconds_difference)
        if abs(seconds_difference) > 60:
            self.roundStartTime = system_time - game_time_delta

        # TODO does a replay show the current game time? probably

    @staticmethod
    def cut_image(img_array, dimensions):
        map_image = img_array[dimensions["start_y"]:dimensions["end_y"], dimensions["start_x"]:dimensions["end_x"]]
        map_image_array = np.asarray(map_image)
        return map_image_array

    def cut_and_threshold(self, img_array, dimensions):
        map_image_array = self.cut_image(img_array, dimensions)
        return self.threshold(map_image_array)

    def get_verified_game_time(self, computer_time):
        time_dictionary = {
            "datetime": self.game_datetime,
            "verified": self.newly_verified_game_time
        }

        # the next tick will be calculated
        if self.newly_verified_game_time:
            self.newly_verified_game_time = False

        return time_dictionary

    @staticmethod
    def save_debug_data(img_array, loop_count, system_time):
        return
        # TODO Update save_debug_data

        path = "Debug"

        # save image
        img = Image.fromarray(img_array)
        img.save(path + "\\Digit " + system_time + " " + str(loop_count) + ".png", "PNG")
        '''
        if (currentTime != "for_reference"):
            #save potential
            debugFile = open(path+"\\Potential " + currentTime + " map.txt",'w')
            for potentialMap, value in sorted(self.potential.items(), key = operator.itemgetter(1), reverse = True):
                lineToWrite = str(value)+': '+potentialMap+'\n'
                debugFile.write(lineToWrite)
        '''
