from PIL import Image
import numpy as np
from datetime import datetime, timedelta

from GameObject import GameObject


class TimeInfo(GameObject):
    def __init__(self, debug_mode):
        self.currentGameTime = datetime.min
        self.mapStartTime = None
        self.digitReferences = self.read_references("Reference\\DigitImageList.txt")
        self.colonReference = self.read_references("Reference\\ColonImageList.txt")
        self.digitDimensions = {
            "start_x": 154,
            "end_x": 162,
            "start_y": 73,
            "end_y": 85
        }

        self.debugMode = debug_mode

    def reset_time(self):
        self.currentGameTime = datetime.min
        self.mapStartTime = None

    def main(self, screen_image_array, computer_time):
        self.identify_time(screen_image_array, computer_time)
        return True

    def identify_time(self, img_array, computer_time):
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
                if potential["colon"] > colon_requirement:
                    # print("Colon!")
                    time_string = time_string + ":"
                    colon_found = True
                    dimensions["start_x"] = dimensions["start_x"] + 4
                    dimensions["end_x"] = dimensions["end_x"] + 4
                    if self.debugMode:
                        self.save_debug_data(this_digit_array, loop_count)
                    loop_count = loop_count + 1
                    continue
                # print("Not Colon")
            this_digit_array = self.cut_and_threshold(img_array, dimensions)
            potential = self.what_image_is_this(this_digit_array, self.digitReferences)
            this_digit_full = max(potential.keys(), key=(lambda k: potential[k]))
            this_digit_split = this_digit_full.split("-")
            this_digit = this_digit_split[0]

            if this_digit == "3" or this_digit == "6" or this_digit == "8":
                if this_digit_array[6][2][0] == 0:
                    this_digit = "3"
                elif this_digit_array[4][6][0] == 0:
                    this_digit = "6"
                else:
                    this_digit = "8"

            # print (this_digit)
            # print (potential)
            time_string = time_string + str(this_digit)
            time_string_split = time_string.split(":")

            if colon_found:
                digits_after_colon = digits_after_colon + 1
            else:
                digits_before_colon = digits_before_colon + 1
            if self.debugMode:
                self.save_debug_data(this_digit_array, loop_count)
            if digits_after_colon == 2:
                break
            dimensions["start_x"] = dimensions["start_x"] + 9
            dimensions["end_x"] = dimensions["end_x"] + 9
            if loop_count > 4:
                break
            else:
                loop_count = loop_count + 1
        if time_string[1] == ":" or time_string[2] == ":":  # assume correct read
            this_time = datetime.strptime(time_string, "%M:%S")
            self.currentGameTime = this_time
            print(datetime.strftime(this_time, "%M:%S"))

            this_time_seconds = int(time_string_split[1])
            this_time_minutes = int(time_string_split[0])
            this_time_delta = timedelta(minutes=this_time_minutes, seconds=this_time_seconds)

            calculated_start_time = computer_time - this_time_delta
            if self.mapStartTime is None:  # and time > 0:00
                self.mapStartTime = calculated_start_time
                print(datetime.strftime(self.mapStartTime, "%H:%M:%S"))

            seconds_difference = (calculated_start_time - self.mapStartTime).total_seconds()
            print(seconds_difference)
            if abs(seconds_difference) > 60:
                self.mapStartTime = computer_time - this_time_delta

        else:
            print("Time not reading correctly")
            # TODO save time debug

    # check to see if the times line up??
    # does a replay show the current game time? probably

    @staticmethod
    def cut_image(img_array, dimensions):
        map_image = img_array[dimensions["start_y"]:dimensions["end_y"], dimensions["start_x"]:dimensions["end_x"]]
        map_image_array = np.asarray(map_image)
        return map_image_array

    def cut_and_threshold(self, img_array, dimensions):
        map_image_array = self.cut_image(img_array, dimensions)
        return self.threshold(map_image_array)

    def get_current_game_time(self, computer_time):
        if self.mapStartTime is not None:
            map_time_delta = computer_time - self.mapStartTime
        else:
            map_time_delta = timedelta(seconds=0)
        map_datetime = datetime.min + map_time_delta
        return map_datetime

    @staticmethod
    def save_debug_data(img_array, loop_count):
        path = "Debug"

        # save image
        img = Image.fromarray(img_array)
        img.save(path + "\\Digit " + str(loop_count) + ".png", "PNG")
        '''
        if (currentTime != "for_reference"):
            #save potential
            debugFile = open(path+"\\Potential " + currentTime + " map.txt",'w')
            for potentialMap, value in sorted(self.potential.items(), key = operator.itemgetter(1), reverse = True):
                lineToWrite = str(value)+': '+potentialMap+'\n'
                debugFile.write(lineToWrite)
        '''
