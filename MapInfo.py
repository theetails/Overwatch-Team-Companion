from PIL import Image
import numpy as np
from scipy.misc import imresize
import operator
from functools import reduce
from GameObject import GameObject


class MapInfo(GameObject):
    mapDictionary = {"dorado": "escort", "eichenwalde": "transition", "hanamura": "assault", "hollywood": "transition",
                     "ilios": "control", "king's row": "transition", "lijiang": "control", "nepal": "control",
                     "numbani": "transition", "oasis": "control", "route66": "escort", "temple of anubis": "assault",
                     "volskaya industries": "assault", "watchpoint gibraltar": "escort", "black forest": "arena",
                     "castillo": "arena", "ecopoint antarctica": "arena", "necropolis": "arena",
                     "horizon lunar colony": "assault", "ilios well": "arena", "oasis city center": "arena",
                     "oasis gardens": "arena"}
    currentMap = [None]
    currentMapType = "escort"
    currentMapSide = "offense"
    mapChange = False

    previousMap = [None]
    previousMapType = None
    previousMapSide = None

    currentImageArray = None
    potential = None
    thisMapPotential = None
    previousImageArray = None
    previousPotential = None

    imageThreshold = {"Hero Select": 1850, "Tab": 1700, "Assault": 135, "Control": 250, "Victory": 6500, "Defeat": 5800}

    def __init__(self, debug_mode):
        self.objectiveProgress = {}
        self.assaultPixelsToCheck = []

        self.debugMode = debug_mode
        self.mapReferences = self.read_references("Reference\\MapImageList.txt")
        self.mapReferencesLijiang = self.read_references("Reference\\MapImageListLijiang.txt")
        self.mapReferencesTab = self.read_references("Reference\\MapImageListTab.txt")
        self.assaultReference = self.read_references("Reference\\ObjectiveListAssault.txt")
        self.controlReference = self.read_references("Reference\\ObjectiveListControl.txt")
        self.gameEndReference = self.read_references("Reference\\GameEnd.txt")

        self.reset_objective_progress()
        self.calculate_assault_progress_pixels()

    def main(self, screen_image_array):
        # check if Tab View
        map_result = self.identify_map(screen_image_array, "Tab")
        if map_result:
            return "Tab"
        else:
            # check if Hero Select View
            map_result = self.identify_map(screen_image_array, "Hero Select")
            if map_result:
                return "Hero Select"
            else:
                return False

    def reset_objective_progress(self):
        self.objectiveProgress = {
            "currentType": None,
            "gameEnd": False,
            "unlocked": False,
            "gameOver": False,
            "assaultPoint": False,
            "assaultPointProgress": []
        }

    def calculate_assault_progress_pixels(self):
        assault_radius = 23  # px
        self.assaultPixelsToCheck = []
        center_points = [[925, 120], [1000, 120]]
        point_number = 0
        for centerPoint in center_points:
            self.assaultPixelsToCheck.append([])
            for percentage in range(0, 100):
                theta = -(percentage - 125) / (5 / 18)
                x_coordinate = int((np.cos(np.deg2rad(theta)) * assault_radius) + centerPoint[0])
                if percentage > 50:  # center isn't perfectly center
                    x_coordinate = x_coordinate - 1
                y_coordinate = int(-(np.sin(np.deg2rad(theta)) * assault_radius) + centerPoint[1])
                if 25 < percentage < 75:  # center isn't perfectly center
                    y_coordinate = y_coordinate + 1
                # print (str(percentage) + " " + str(theta) + " " + str(x_coordinate) + " " + str(y_coordinate))
                self.assaultPixelsToCheck[point_number].append([x_coordinate, y_coordinate])
            point_number = point_number + 1

    def map_type(self):
        return self.mapDictionary[self.currentMap[0]]

    def identify_map(self, screen_img_array, view):
        potential = None

        this_map_array = self.get_map(screen_img_array, view, False)
        if view == "Hero Select":
            potential = self.what_image_is_this(this_map_array, self.mapReferences)
            self.objectiveProgress["gameEnd"] = None  # delete me with proper flow
        elif view == "Tab":
            potential = self.what_image_is_this(this_map_array, self.mapReferencesTab)
        this_map = max(potential.keys(), key=(lambda k: potential[k]))
        self.previousImageArray = self.currentImageArray
        self.currentImageArray = this_map_array
        self.previousPotential = self.potential
        self.potential = potential
        self.thisMapPotential = potential[this_map]

        if potential[this_map] > self.imageThreshold[view]:
            if this_map == "lijiang tower" and view == "Hero Select":
                this_map = self.get_map(screen_img_array, "Hero Select", True)
                potential = self.what_image_is_this(this_map, self.mapReferencesLijiang)
                this_map = max(potential.keys(), key=(lambda k: potential[k]))
                this_map = "lijiang-" + this_map
            this_map_split = this_map.split("-")
            if self.currentMap[0] != this_map_split[0]:
                print("Map Changed")
                self.mapChange = True
            else:
                self.mapChange = False
            self.previousMap = self.currentMap
            self.currentMap = this_map_split
            print(this_map)
            return True
        else:
            return False

    def identify_map_type(self):
        if self.currentMap[0] != self.previousMap[0]:
            if self.currentMap[0] != "unknown":
                this_map_type = self.map_type()
                # temporary until detecting during tab
                if this_map_type == "transition":
                    this_map_type = "assault"
            else:
                this_map_type = "control"

            self.previousMapType = self.currentMapType
            self.currentMapType = this_map_type
            return_value = True
        else:
            return_value = False

        print(self.currentMapType)
        return return_value

    def save_debug_data(self, current_time):
        path = "Debug"

        # save image
        img = Image.fromarray(self.currentImageArray)
        img.save(path + "\\Potential " + current_time + " map.png", "PNG")
        if current_time != "for_reference":
            # save potential
            debug_file = open(path + "\\Potential " + current_time + " map.txt", 'w')
            for potentialMap, value in sorted(self.potential.items(), key=operator.itemgetter(1), reverse=True):
                line_to_write = str(value) + ': ' + potentialMap + '\n'
                debug_file.write(line_to_write)

    def get_map(self, img_array, mode, lijiang):
        start_x = None
        end_x = None
        start_y = None
        end_y = None
        scaled_image_array = None

        if mode == "Hero Select":
            start_x = 60
            end_x = 290
            if lijiang:
                start_x = 294  # lijiang subsection
                end_x = 420  # lijiang subsection
            start_y = 168
            end_y = 206
        elif mode == "Tab":
            start_x = 105
            end_x = 240
            start_y = 49
            end_y = 62
        map_image = img_array[start_y:end_y, start_x:end_x]
        map_image_array = np.asarray(map_image)
        if mode == "Hero Select":
            scaled_image_array = imresize(map_image_array, (19, 115))
        elif mode == "Tab":
            scaled_image_array = map_image_array
        new_image_array = self.threshold(scaled_image_array)
        return new_image_array

    def identify_side(self, img_array):
        pixel_to_check = img_array[95][95]
        this_side = self.team_from_pixel(pixel_to_check)
        print(this_side)

        if this_side == "neither":
            this_side = self.previousMapSide

        if this_side != self.previousMapSide:
            self.previousMapSide = self.currentMapSide
            self.currentMapSide = this_side
            return True
        else:
            return False

    @staticmethod
    def team_from_pixel(pixel_to_check):
        red = pixel_to_check[0]
        green = pixel_to_check[1]
        blue = pixel_to_check[2]
        # print(red)
        # print(green)
        # print(blue)
        if (red > 195) and (green < 200) and (blue < 200):
            this_side = "offense"
        elif (red < 200) and (green > 180) and (blue > 100):
            this_side = "defense"
        else:
            this_side = "neither"
        # print ("rgb: " + str(red) + "," + str(green) + "," + str(blue))
        return this_side

    def identify_objective_progress(self, img_array, mode="standard"):
        if self.currentMap == [None] or self.objectiveProgress["gameOver"] is True:
            return False

        map_type = self.map_type()
        new_image_array = None

        if map_type == "transition":
            # need to go from assault to escort
            if self.objectiveProgress["currentType"] is None:
                self.objectiveProgress["currentType"] = "assault"

        if map_type == "assault" or self.objectiveProgress["currentType"] == "assault":
            new_image_array = self.identify_assault_objective_progress(img_array, map_type, mode)

        if map_type == "control" or self.objectiveProgress["currentType"] == "control":
            new_image_array = self.identify_control_objective_progress(img_array, mode)

        if map_type == "escort" or self.objectiveProgress["currentType"] == "escort":
            new_image_array = self.identify_escort_objective_progress(img_array, map_type, mode)

        if mode == "for_reference":
            path = "Debug"
            # save image
            img = Image.fromarray(new_image_array)
            img.save(path + "\\Potential Objective.png", "PNG")

    def identify_assault_objective_progress(self, img_array, map_type, mode="standard"):
        dimensions = {}
        check_game_end = False
        new_image_array = None
        this_status = None
        potential = None

        if self.objectiveProgress["assaultPoint"] == "B":
            check_assault_point2 = True
        else:
            check_assault_point2 = False

        if self.objectiveProgress["assaultPoint"] != "B":
            # Assault Point 1
            dimensions["start_x"] = 918
            dimensions["end_x"] = 930
            dimensions["start_y"] = 114
            dimensions["end_y"] = 128
            # color for side
            # pixel_to_check = img_array[108][927]

            new_image_array = self.cut_and_threshold(img_array, dimensions)
            potential = self.what_image_is_this(new_image_array, self.assaultReference)
            this_status = max(potential.keys(), key=(lambda k: potential[k]))

            if potential[this_status] > self.imageThreshold["Assault"]:  # max 166?
                this_status_split = this_status.split("-")
                this_status = this_status_split[0]
                if this_status == "Done":
                    if map_type == "transition":
                        print("Transition to Escort")
                        self.objectiveProgress["currentType"] = "escort"
                        return
                    else:
                        check_assault_point2 = True
                elif this_status != "Locked":
                    self.identify_assault_point_progress(img_array, 0, mode)
            elif map_type == "transition":
                dimensions["start_x"] = 760
                dimensions["end_x"] = 772
                dimensions["start_y"] = 114
                dimensions["end_y"] = 128
                new_image_array = self.cut_and_threshold(img_array, dimensions)
                potential = self.what_image_is_this(new_image_array, self.assaultReference)
                this_status = max(potential.keys(), key=(lambda k: potential[k]))
                this_status_split = this_status.split("-")
                this_status = this_status_split[0]
                if potential[this_status] > self.imageThreshold["Assault"] and (this_status == "Locked"
                                                                                or this_status_split[0] == "Done"):
                    print("Transition to Escort")
                    self.objectiveProgress["currentType"] = "escort"
                    return
                else:
                    check_game_end = True
        if check_assault_point2:
            # Assault Point 2
            dimensions["start_x"] = 994
            dimensions["end_x"] = 1006
            dimensions["start_y"] = 114
            dimensions["end_y"] = 128
            # pixel_to_check = img_array[108][997]
            new_image_array = self.cut_and_threshold(img_array, dimensions)
            potential = self.what_image_is_this(new_image_array, self.assaultReference)
            this_status = max(potential.keys(), key=(lambda k: potential[k]))
            this_status_split = this_status.split("-")
            this_status = this_status_split[0]
            if potential[this_status] > self.imageThreshold["Assault"]:
                self.identify_assault_point_progress(img_array, 1, mode)
            else:
                print(2)
                check_game_end = True
        if check_game_end:
            self.identify_game_end(img_array, mode)
        else:
            # if this_status != "Locked":
                # Do I need to use this?
                # this_side = self.teamFromPixel(pixel_to_check)
            # print(this_side)
            if this_status != self.objectiveProgress["assaultPoint"]:
                self.objectiveProgress["assaultPoint"] = this_status
                print(this_status)
                print(potential)

        return new_image_array

    def identify_assault_point_progress(self, img_array, point_number, mode="standard"):
        assault_percent_complete = 0
        for pixelCoordinates in self.assaultPixelsToCheck[point_number]:
            this_pixel = img_array[pixelCoordinates[1]][pixelCoordinates[0]]
            avg_color_brightness = reduce(lambda x, y: int(x) + int(y), this_pixel[:3]) / 3
            if avg_color_brightness > 248:
                assault_percent_complete = assault_percent_complete + 1
            elif mode != "standard":
                print(pixelCoordinates)
                print(this_pixel)

        self.objectiveProgress["assaultPointProgress"].append(assault_percent_complete)
        # if len(self.objectiveProgress["assaultPointProgress"] > 3):
        # self.objectiveProgress["assaultPointProgress"].pop(0)
        # if assault_percent_complete >
        # for percentage in self.objectiveProgress["assaultPointProgress"]:
        # True
        # if self.objectiveProgress["assaultPointProgress"]:
        print(assault_percent_complete)

    def identify_control_objective_progress(self, img_array, mode="standard"):
        dimensions = {
            'start_x': 952,
            'end_x': 968,
            'start_y': 78,
            'end_y': 102
        }

        pixel_to_check = {
            'current': img_array[108][959],
            'left': {
                0: img_array[91][774],
                1: img_array[91][814]
            },
            'right': {
                0: img_array[91][1146],
                1: img_array[91][1106]
            }
        }

        new_image_array = self.cut_and_threshold(img_array, dimensions)
        potential = self.what_image_is_this(new_image_array, self.controlReference)
        this_status = max(potential.keys(), key=(lambda k: potential[k]))

        # max 384, lower limit: 250
        if potential[this_status] > self.imageThreshold["Control"]:
            print(this_status)
            print(potential)
            if this_status != "Locked":
                this_side = self.team_from_pixel(pixel_to_check["current"])
                print("Current Controller: " + this_side)
            for pixelIndex, thisPixel in pixel_to_check["left"].items():
                team_result = self.team_from_pixel(thisPixel)
                if team_result == "neither":
                    print("Our Team Progress: " + str(pixelIndex))
                    break
            for pixelIndex, thisPixel in pixel_to_check["right"].items():
                team_result = self.team_from_pixel(thisPixel)
                if team_result == "neither":
                    print("Their Team Progress: " + str(pixelIndex))
                    break
        else:
            self.identify_game_end(img_array, mode)

        return new_image_array

    def identify_escort_objective_progress(self, img_array, map_type, mode="standard"):
        dimensions = {}

        if "escortProgress" not in self.objectiveProgress:
            self.objectiveProgress["escortProgress"] = []

        if map_type == "escort" and self.objectiveProgress["unlocked"] is False:
            # check for lock symbol
            dimensions["start_x"] = 953
            dimensions["end_x"] = 965
            dimensions["start_y"] = 111
            dimensions["end_y"] = 125

            new_image_array = self.cut_and_threshold(img_array, dimensions)
            lock_reference = {
                "Locked": self.assaultReference["Locked"]
            }
            potential = self.what_image_is_this(new_image_array, lock_reference)

            if potential["Locked"] > self.imageThreshold["Assault"]:  # max 166?
                print("Locked")
                print(potential)
                if mode == "for_reference":
                    path = "Debug"
                    # save image
                    img = Image.fromarray(new_image_array)
                    img.save(path + "\\Potential Objective.png", "PNG")
                return
        dimensions["start_x"] = 787
        dimensions["end_x"] = 1135
        dimensions["start_y"] = 118
        dimensions["end_y"] = 128

        if map_type == "transition":
            dimensions["start_x"] = 824
            dimensions["end_x"] = 1172

        # dorodo point 1: 32%
        # dorodo point 2: 68%
        # route66 point 1: 34%
        # route66 point 2: 70%
        # watchpoint point 1: 33%
        # watchpoint point 2: 66%
        # eichenwalde point 1: 66%
        # eichenwalde point 1: 74% (Free move after door)
        # hollywood point 1: 61%
        # king's row point 1: 62%
        # numbani point 1: 58%

        new_image_array = self.cut_image(img_array, dimensions)
        end_found = False
        percent_complete = None

        for X in range(0, (dimensions["end_x"] - dimensions["start_x"])):

            pixel_to_check = new_image_array[5][X]
            pixel_team = self.team_from_pixel(pixel_to_check)
            if pixel_team != self.currentMapSide:
                percent_complete = round(X / (dimensions["end_x"] - dimensions["start_x"]) * 100)
                print("Percent Complete: " + str(percent_complete))
                end_found = True
                break

        if not end_found:
            percent_complete = 100
            print("Percent Complete: 100 - Complete Color Change")

        escort_progress_length = len(self.objectiveProgress["escortProgress"])
        if percent_complete > 0 or escort_progress_length > 0:
            self.objectiveProgress["escortProgress"].append(percent_complete)

        # check to see if we can confirm the match has started, unlocking the Escort Objective
        if escort_progress_length > 2:
            minimum = 101
            maximum = -1
            for thisEscortProgress in self.objectiveProgress["escortProgress"][-3:]:  # last 3
                if thisEscortProgress > maximum:
                    maximum = thisEscortProgress
                if thisEscortProgress < minimum:
                    minimum = thisEscortProgress
            if minimum != 0 and (maximum - minimum) < 5:
                self.objectiveProgress["unlocked"] = True

        if percent_complete == 0:
            self.identify_game_end(img_array, mode)

        return new_image_array

    def identify_game_end(self, img_array, mode="standard"):
        dimensions = {
            'start_x': 643,
            'end_x': 1305,
            'start_y': 440,
            'end_y': 633
        }
        cropped_image_array = self.cut_image(img_array, dimensions)
        # -- Check for Victory  -- #
        # convert to black and white based on yellow
        yellow = [230, 205, 100]
        result = self.game_end_format_image(cropped_image_array, yellow, "Victory")
        if type(result) is not bool:
            reference_dictionary = {
                'Victory': self.gameEndReference["Victory"]
            }
            potential = self.what_image_is_this(np.asarray(result), reference_dictionary)
            print(potential)
            if potential["Victory"] > self.imageThreshold["Victory"]:
                self.objectiveProgress["gameEnd"] = "Victory"
                print("Victory!")
                self.submit_stats_and_clear()
        if self.objectiveProgress["gameEnd"] != "Victory":
            # -- Check for Defeat -- #
            red = [210, 120, 130]
            result = self.game_end_format_image(cropped_image_array, red, "Defeat")
            if type(result) is not bool:
                reference_dictionary = {
                    'Defeat': self.gameEndReference["Defeat"]
                }
                potential = self.what_image_is_this(np.asarray(result), reference_dictionary)
                print(potential)
                if potential["Defeat"] > self.imageThreshold["Defeat"]:  # max 7200
                    self.objectiveProgress["gameEnd"] = "Defeat"
                    print("Defeat! :(")
                    self.submit_stats_and_clear()
        if (type(result) is not bool) and (mode == "for_reference"):
            path = "Debug"
            # save image
            result.save(path + "\\Game End.png", "PNG")

    def game_end_format_image(self, image_array, color, mode):
        cropped_image_array = image_array.copy()
        cropped_image_array.setflags(write=True)

        img = Image.fromarray(cropped_image_array)
        cropped_image_array = np.asarray((img.resize((200, 56), Image.BILINEAR)))
        cropped_image_array.setflags(write=True)

        black_check_column = {}
        rows_to_cut = []
        columns_to_cut = []
        cropped_image_array_length = len(cropped_image_array) - 1
        previous_row = None
        previous_column = None

        for rowNumber, eachRow in enumerate(cropped_image_array):
            black_check_row = True

            for pixelNumber, eachPixel in enumerate(eachRow):

                if rowNumber == 0:
                    black_check_column[pixelNumber] = True

                go_white = False
                if mode == "Victory":
                    if (eachPixel[0] > color[0]) \
                            and (eachPixel[1] > color[1]) \
                            and (eachPixel[2] < color[2]):  # greater, greater, less
                        go_white = True
                elif mode == "Defeat":
                    if (eachPixel[0] > color[0]) \
                            and (eachPixel[1] < color[1]) \
                            and (eachPixel[2] < color[2]):  # greater, less, less
                        go_white = True
                if go_white:
                    cropped_image_array[rowNumber][pixelNumber] = [255, 255, 255]  # White
                    black_check_row = False
                    black_check_column[pixelNumber] = False
                else:
                    cropped_image_array[rowNumber][pixelNumber] = [0, 0, 0]  # Black
                # crop box where entire column is black

                if rowNumber == cropped_image_array_length and black_check_column[pixelNumber] is True:
                    columns_to_cut.append(pixelNumber)
            # crop box where entire row is black
            if black_check_row:
                rows_to_cut.append(rowNumber)

        new_dimensions = {}
        # cut top edge
        for index, this_row in enumerate(rows_to_cut):
            if index != 0:
                if previous_row + 1 != this_row:
                    new_dimensions["start_y"] = previous_row
                    break
            previous_row = this_row
        # cut bottom edge
        for index, this_row in enumerate(reversed(rows_to_cut)):
            if index != 0:
                if previous_row - 1 != this_row:
                    new_dimensions["end_y"] = previous_row
                    break
            previous_row = this_row
        # far left  --  Only crop far left and right, not between letters
        for index, thisColumn in enumerate(columns_to_cut):
            if index != 0:
                if previous_column + 1 != thisColumn:
                    new_dimensions["start_x"] = previous_column
                    break
            previous_column = thisColumn
        # far right
        for index, thisColumn in enumerate(reversed(columns_to_cut)):
            if index != 0:
                if previous_column - 1 != thisColumn:
                    new_dimensions["end_x"] = previous_column
                    break
            previous_column = thisColumn
        if ("start_y" not in new_dimensions) \
                or ("end_y" not in new_dimensions) \
                or ("start_x" not in new_dimensions) \
                or ("end_x" not in new_dimensions):
            path = "Debug"
            # save image
            img = Image.fromarray(cropped_image_array)
            img.save(path + "\\" + mode + ".png", "PNG")
            return False
        new_cropped_image_array = self.cut_image(cropped_image_array, new_dimensions)
        img = Image.fromarray(new_cropped_image_array)
        scaled_image_array = self.threshold(np.asarray((img.resize((160, 45), Image.BILINEAR))))
        scaled_image = Image.fromarray(scaled_image_array)

        if len(scaled_image_array[0]) * len(scaled_image_array) != len(self.gameEndReference["Victory"][0]):
            return False
        else:
            return scaled_image

    @staticmethod
    def cut_image(img_array, dimensions):
        map_image = img_array[dimensions["start_y"]:dimensions["end_y"], dimensions["start_x"]:dimensions["end_x"]]
        map_image_array = np.asarray(map_image)
        return map_image_array

    def cut_and_threshold(self, img_array, dimensions):
        map_image_array = self.cut_image(img_array, dimensions)
        return self.threshold(map_image_array)

    def broadcast_options(self, broadcaster):
        this_map = [
            self.currentMapSide,  # side options: offense, defense
            self.currentMapType,  # type options: escort, assault, control
            "single_hero"
        ]

        options_to_send = ["options", this_map]
        if broadcaster != "debug":
            broadcaster.publish(broadcaster.subscriptionString, options_to_send)

    def submit_stats_and_clear(self):
        self.objectiveProgress["gameOver"] = True
        print("Submit Stats and Clear")
