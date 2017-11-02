from PIL import Image
import numpy as np
from scipy.misc import imresize
import operator
from functools import reduce
import copy

from GameObject import GameObject


class MapInfo(GameObject):
    mapDictionary = {
        # escort
        "hanamura": "assault", "horizon lunar colony": "assault", "temple of anubis": "assault",
        "volskaya industries": "assault",
        # transition
        "eichenwalde": "transition", "hollywood": "transition", "king's row": "transition", "numbani": "transition",
        # control
        "ilios": "control", "lijiang": "control", "nepal": "control", "oasis": "control",
        # escort
        "dorado": "escort", "junkertown": "escort", "route66": "escort", "watchpoint gibraltar": "escort",
        # arena
        "black forest": "arena", "castillo": "arena", "chateau guillard": "arena", "ecopoint antarctica": "arena",
        "ilios lighthouse": "arena", "ilios ruins": "arena", "ilios well": "arena", "lijiang control center": "arena",
        "lijiang garden": "arena", "lijiang night market": "arena", "necropolis": "arena", "nepal sanctum": "arena",
        "nepal shrine": "arena", "nepal village": "arena", "oasis city center": "arena", "oasis gardens": "arena",
        "oasis university": "arena"
    }
    current_map = [None]
    currentMapSide = "offense"
    mapChange = False

    previousMap = [None]
    previousMapSide = None

    currentImageArray = None
    potential = None
    thisMapPotential = None
    previousImageArray = None
    previousPotential = None

    imageThreshold = {
        "Hero Select": 1875,
        "Tab": 1850,  # was 1710
        "Assault": 135,
        "Control": 270,  # max 384, lower limit: 250
        "Victory": 6500,
        "Defeat": 5800
    }

    def __init__(self, game_version, debug_mode):
        self.competitive = True;
        self.objectiveProgress = {}
        self.assaultPixelsToCheck = []

        self.game_version = game_version
        self.debugMode = debug_mode
        self.mapReferences = {
            "Hero Select": self.read_references("Reference\\MapImageList.txt"),
            "Tab": self.read_references("Reference\\MapImageListTab.txt"),
            "Lijiang": self.read_references("Reference\\MapImageListLijiang.txt"),
            "High Threshold": self.read_references("Reference\\MapImageHighThreshold.txt")
        }

        self.assaultReference = self.read_references("Reference\\ObjectiveListAssault.txt")
        self.controlReference = self.read_references("Reference\\ObjectiveListControl.txt")
        self.gameEndReference = self.read_references("Reference\\GameEnd.txt")

        self.calculate_assault_progress_pixels()

        self.dimensions = self.dimensions_from_version()

    def main(self, screen_image_array, current_time):
        # check if Tab View
        map_result = self.identify_map(screen_image_array, "Tab")
        if map_result:
            this_view = "Tab"
        else:
            # check if Hero Select View
            map_result = self.identify_map(screen_image_array, "Hero Select")
            if map_result:
                this_view = "Hero Select"
            else:
                this_view = False

                # TODO check if removable
                # if (self.thisMapPotential < self.imageThreshold[this_view]) and self.debugMode:
                # self.save_debug_data(current_time)

        return this_view

    def reset_objective_progress(self):
        self.objectiveProgress = {
            "currentType": None,
            "gameEnd": False,
            "gameOver": False
        }

        map_type = self.map_type()

        if map_type == "assault" or map_type == "transition":
            self.objectiveProgress["assaultPoint"] = False
            self.objectiveProgress["assaultPointProgress"] = None
        if map_type == "control":
            self.objectiveProgress["controlProgress"] = [None, None, None, None]
        if map_type == "escort" or map_type == "transition":
            self.objectiveProgress["escortProgress"] = []
            self.objectiveProgress["unlocked"] = False

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
        if self.current_map[0] is None:
            return "assault"
        else:
            return self.mapDictionary[self.current_map[0]]

    def identify_map(self, screen_img_array, view):
        potential = None

        this_map_array = self.get_map(screen_img_array, view)
        potential = self.what_image_is_this(this_map_array, self.mapReferences[view])
        this_map = max(potential.keys(), key=(lambda k: potential[k]))
        self.previousImageArray = self.currentImageArray
        self.currentImageArray = this_map_array
        self.previousPotential = self.potential
        self.potential = potential
        self.thisMapPotential = potential[this_map]
        if potential[this_map] > self.imageThreshold[view]:
            print(str(potential[this_map]) + " " + this_map)
            if this_map == "lijiang tower" and view == "Hero Select":
                this_map_lijiang = self.get_map(screen_img_array, "Hero Select", lijiang=True)
                potential = self.what_image_is_this(this_map_lijiang, self.mapReferences["Lijiang"])
                this_map_lijiang = max(potential.keys(), key=(lambda k: potential[k]))
                this_map = "lijiang-" + this_map_lijiang
            this_map_split = this_map.split("-")
            if self.current_map[0] != this_map_split[0]:
                print("Map Changed")
                self.mapChange = True
            else:
                self.mapChange = False
            self.previousMap = self.current_map
            self.current_map = this_map_split
            return True
        elif view == "Hero Select":
            this_map_array = self.get_map(screen_img_array, view, threshold_balance=True)
            potential = self.what_image_is_this(this_map_array, self.mapReferences["High Threshold"])
            this_map = max(potential.keys(), key=(lambda k: potential[k]))
            if potential[this_map] > self.imageThreshold[view]:
                this_map_split = this_map.split("-")
                if self.current_map[0] != this_map_split[0]:
                    print("Map Changed")
                    self.mapChange = True
                else:
                    self.mapChange = False
                self.previousMap = self.current_map
                self.current_map = this_map_split
                print(this_map)
                return True
            else:
                return False
        else:
            return False

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

    def get_map(self, img_array, mode, lijiang=False, threshold_balance=False):
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
            start_x = 65
            end_x = 220
            start_y = 34
            end_y = 47
        map_image = img_array[start_y:end_y, start_x:end_x]
        map_image_array = np.asarray(map_image)

        if mode == "Hero Select":
            scaled_image_array = imresize(map_image_array, (19, 115))
        elif mode == "Tab":
            scaled_image_array = map_image_array

        if not threshold_balance:
            new_image_array = self.threshold(scaled_image_array)
        else:
            new_image_array = self.image_to_black_and_white(scaled_image_array, 252)
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
            # print("Neither")
            # print("rgb: " + str(red) + "," + str(green) + "," + str(blue))
        return this_side

    @staticmethod
    def team_from_pixel_precise(pixel_to_check, opposite=False):
        red = pixel_to_check[0]
        green = pixel_to_check[1]
        blue = pixel_to_check[2]
        # print(red)
        # print(green)
        # print(blue)
        if (175 <= red <= 255) and (0 <= green <= 200) and (0 <= blue <= 200):
            this_side = "offense"
        elif (40 <= red <= 215) and (155 <= green <= 255) and (195 <= blue <= 255):
            this_side = "defense"
        else:
            this_side = "neither"
            # print("Neither")
            # print("rgb: " + str(red) + "," + str(green) + "," + str(blue))
        if opposite:
            switcher = {
                "offense": "defense",
                "defense": "offense",
                "neither": "neither"
            }
            this_side = switcher[this_side]
        return this_side

    def identify_objective_progress(self, img_array, mode="standard"):
        if "gameOver" not in self.objectiveProgress:
            return False
        if self.current_map == [None] or self.objectiveProgress["gameOver"] is True:
            return False
        map_type = self.map_type()
        new_image_array = None
        if map_type == "transition":
            # need to go from assault to escort
            if self.objectiveProgress["currentType"] is None:
                self.objectiveProgress["currentType"] = "assault"
        else:
            self.objectiveProgress["currentType"] = map_type

        if self.objectiveProgress["currentType"] == "assault":
            new_image_array = self.identify_assault_objective_progress(img_array, map_type, mode)

        if self.objectiveProgress["currentType"] == "control":
            new_image_array = self.identify_control_objective_progress(img_array, mode)

        if self.objectiveProgress["currentType"] == "escort":
            new_image_array = self.identify_escort_objective_progress(img_array, map_type, mode)

        if mode == "for_reference":
            path = "Debug"
            # save image
            img = Image.fromarray(new_image_array)
            img.save(path + "\\Potential Objective.png", "PNG")

    def identify_assault_objective_progress(self, img_array, map_type, mode="standard"):
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
            # color for side
            # pixel_to_check = img_array[108][927]

            new_image_array = self.cut_and_threshold(img_array, self.dimensions["assault"]["point1"])
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
                new_image_array = self.cut_and_threshold(img_array, self.dimensions["assault"]["transition"])
                potential = self.what_image_is_this(new_image_array, self.assaultReference)
                this_status_key = max(potential.keys(), key=(lambda k: potential[k]))
                this_status_split = this_status_key.split("-")
                this_status = this_status_split[0]
                if potential[this_status_key] > self.imageThreshold["Assault"] and \
                        (this_status == "Locked" or this_status == "Done"):
                    print("Transition to Escort")
                    self.objectiveProgress["currentType"] = "escort"
                    return
                else:
                    check_game_end = True
        if check_assault_point2:
            # Assault Point 2
            # pixel_to_check = img_array[108][997]
            new_image_array = self.cut_and_threshold(img_array, self.dimensions["assault"]["point2"])
            potential = self.what_image_is_this(new_image_array, self.assaultReference)
            this_status = max(potential.keys(), key=(lambda k: potential[k]))
            this_status_split = this_status.split("-")
            this_status = this_status_split[0]
            if potential[this_status] > self.imageThreshold["Assault"]:
                self.identify_assault_point_progress(img_array, 1, mode)
            else:
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

        self.objectiveProgress["assaultPointProgress"] = assault_percent_complete
        print(assault_percent_complete)

    def identify_control_objective_progress(self, img_array, mode="standard"):
        pixel_current_height = 118  # 1.16 108
        pixel_side_height = 91
        reference = self.controlReference
        status_addendum = ""
        new_image_array = self.cut_and_threshold(img_array, self.dimensions["control"]["normal"])
        objective_identified = self.identify_control_core(img_array, new_image_array, pixel_current_height,
                                                          pixel_side_height, reference, status_addendum)

        if objective_identified is False:
            # check if locked between rounds
            pixel_current_height = 145
            pixel_side_height = 128
            reference = {"Prepare": self.controlReference["Locked"]}
            status_addendum = ""
            new_image_array = self.cut_and_threshold(img_array, self.dimensions["control"]["locked"])
            objective_identified = self.identify_control_core(img_array, new_image_array, pixel_current_height,
                                                              pixel_side_height, reference, status_addendum)
            if objective_identified is False:
                # check for overtime
                pixel_current_height = 163
                pixel_side_height = 146
                reference = self.controlReference
                status_addendum = "-Overtime"
                new_image_array = self.cut_and_threshold(img_array, self.dimensions["control"]["overtime"])
                objective_identified = self.identify_control_core(img_array, new_image_array, pixel_current_height,
                                                                  pixel_side_height, reference, status_addendum)
                if objective_identified is False:
                    self.identify_game_end(img_array, mode)

        return new_image_array

    def identify_control_core(self, img_array, new_image_array, pixel_current_height, pixel_side_height, reference,
                              status_addendum):
        this_side = "neither"

        our_progress = 0
        their_progress = 0

        potential = self.what_image_is_this(new_image_array, reference)
        this_status = max(potential.keys(), key=(lambda k: potential[k]))
        if potential[this_status] > self.imageThreshold["Control"]:
            pixel_to_check = {
                'current': img_array[pixel_current_height][959],
                'left': {
                    0: img_array[pixel_side_height][774],
                    1: img_array[pixel_side_height][814]
                },
                'right': {
                    0: img_array[pixel_side_height][1146],
                    1: img_array[pixel_side_height][1106]
                }
            }
            if this_status not in ["Locked", "Prepare"]:
                this_side = self.team_from_pixel(pixel_to_check["current"])
                print("Current Controller: " + this_side)
            if not self.competitive:
                for pixelIndex, thisPixel in pixel_to_check["left"].items():
                    team_result = self.team_from_pixel(thisPixel)
                    if team_result == "neither":
                        our_progress = pixelIndex
                        break
                for pixelIndex, thisPixel in pixel_to_check["right"].items():
                    team_result = self.team_from_pixel(thisPixel)
                    if team_result == "neither":
                        their_progress = pixelIndex
                        break
            if self.objectiveProgress["controlProgress"][1] != our_progress or \
                    self.objectiveProgress["controlProgress"][2] != their_progress:
                print("Game Progress | Us: " + str(our_progress) + "   Them: " + str(their_progress))
            print("Game Progress | Us: " + str(our_progress) + "   Them: " + str(their_progress))

            this_status = this_status + status_addendum
            if this_status != self.objectiveProgress["controlProgress"][0]:
                print(this_status)
            self.objectiveProgress["controlProgress"] = [this_status, our_progress, their_progress, this_side]
            return True
        else:
            return False

    def identify_escort_objective_progress(self, img_array, map_type, mode="standard"):
        self.competitive = self.identify_competitive(img_array, self.currentMapSide, mode)
        if self.competitive:
            competitive_string = "competitive"
        else:
            competitive_string = "quick"
        print("Competitive: " + str(self.competitive))
        # TODO adjust y values if competitive
        if map_type == "escort" and self.objectiveProgress["unlocked"] is False:
            # check for lock symbol

            new_image_array = self.cut_and_threshold(img_array, self.dimensions["escort"][competitive_string]["lock"])
            lock_reference = {
                "Locked": self.assaultReference["Locked"]
            }
            potential = self.what_image_is_this(new_image_array, lock_reference)

            if potential["Locked"] > self.imageThreshold["Assault"]:  # max 166?
                print("Locked")
                # print(potential)
                if mode == "for_reference":
                    path = "Debug"
                    # save image
                    img = Image.fromarray(new_image_array)
                    img.save(path + "\\Potential Objective.png", "PNG")
                return new_image_array

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
        # TODO junkertown points

        new_image_array = self.cut_image(img_array,
                                         self.dimensions["escort"][competitive_string]["progress_bar"][map_type])
        end_found = False
        percent_complete = None

        dimensions = self.dimensions["escort"][competitive_string]["progress_bar"][map_type]

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

        # check to see if we can confirm the statistics has started, unlocking the Escort Objective

        self.objectiveProgress["escortProgress"].append(percent_complete)

        if escort_progress_length > 2:
            if self.objectiveProgress["unlocked"] is False:
                minimum = 101
                maximum = -1
                for thisEscortProgress in self.objectiveProgress["escortProgress"]:
                    if thisEscortProgress > maximum:
                        maximum = thisEscortProgress
                    if thisEscortProgress < minimum:
                        minimum = thisEscortProgress
                if minimum != 0 and (maximum - minimum) < 5:
                    self.objectiveProgress["unlocked"] = True

            del self.objectiveProgress["escortProgress"][0]

        # print(str(self.objectiveProgress["escortProgress"]))

        if percent_complete == 0:
            self.identify_game_end(img_array, mode)

        return new_image_array

    def identify_competitive(self, img_array, team_side, mode="standard"):
        dimensions = {
            'offense': {
                'start_x': 760,
                'end_x': 880,
                'y': 84
            }, 'defense': {
                'start_x': 1030,
                'end_x': 1180,
                'y': 84
            }
        }
        # check to see if there is a red or blue box (depending on team)
        box_beginning = 0
        box_end = 0
        for X in range(self.dimensions["competitive"][team_side]["start_x"],
                       self.dimensions["competitive"][team_side]["end_x"]):
            pixel_to_check = img_array[self.dimensions["competitive"][team_side]["y"]][X]
            pixel_side = self.team_from_pixel_precise(pixel_to_check, opposite=True)
            # print(str(X) + " " + str(pixel_to_check) + " " + pixel_side)
            if pixel_side == team_side and box_beginning == 0:
                box_beginning = X
            elif pixel_side == "neither" and box_beginning != 0 and box_end == 0:
                if 47 <= (X - box_beginning) <= 124:  # Approximate size of box, may be larger when in bright light
                    box_end = X
                    # print(str(box_beginning) + " " + str(box_end))
                    # TODO if yes, grab current score
                    return True
                else:
                    box_beginning = 0
        return False
        # TODO make sure this is done infrequently, such as only after a tab or hero select

    def identify_game_end(self, img_array, mode="standard"):
        print("Identify Game End")
        if self.competitive:
            competitive_string = "competitive"
        else:
            competitive_string = "quick"
        cropped_image_array = self.cut_image(img_array, self.dimensions["game_end"][competitive_string])
        # -- Check for Victory  -- #
        # convert to black and white based on yellow
        yellow = [230, 205, 135]
        result = self.game_end_format_image(cropped_image_array, yellow, "Victory")
        if type(result) is not bool:
            reference_dictionary = {
                'Victory': self.gameEndReference["Victory"]
            }
            potential = self.what_image_is_this(np.asarray(result), reference_dictionary)
            if potential["Victory"] > self.imageThreshold["Victory"]:
                self.objectiveProgress["gameEnd"] = "Victory"
                print("Victory!")
                self.set_game_over()
            print(potential)
        if self.objectiveProgress["gameEnd"] != "Victory":
            # -- Check for Defeat -- #
            red = [210, 120, 130]
            result = self.game_end_format_image(cropped_image_array, red, "Defeat")
            if type(result) is not bool:
                reference_dictionary = {
                    'Defeat': self.gameEndReference["Defeat"]
                }
                potential = self.what_image_is_this(np.asarray(result), reference_dictionary)
                if potential["Defeat"] > self.imageThreshold["Defeat"]:  # max 7200
                    self.objectiveProgress["gameEnd"] = "Defeat"
                    print("Defeat! :(")
                    self.set_game_over()
        if (mode == "for_reference") and (type(result) is not bool):
            path = "Debug"
            # save image
            result.save(path + "\\Game End.png", "PNG")

    def game_end_format_image(self, image_array, color, mode):
        cropped_image_array = image_array.copy()
        cropped_image_array.setflags(write=True)

        # img = Image.fromarray(cropped_image_array)
        # cropped_image_array = np.asarray((img.resize((200, 56), Image.BILINEAR)))
        # cropped_image_array.setflags(write=True)

        black_check_column = {}
        rows_to_cut = []
        columns_to_cut = []
        cropped_image_array_length = len(cropped_image_array) - 1
        previous_row = None
        previous_column = None

        # threshold image to B&W
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

        # cut image where entire rows are black
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
        column_names = ("start_y", "end_y", "start_x", "start_y")
        if not all(name in new_dimensions for name in column_names):
            return False

        # save image
        path = "Debug"
        img = Image.fromarray(cropped_image_array)
        img.save(path + "\\" + mode + ".png", "PNG")

        new_cropped_image_array = self.cut_image(cropped_image_array, new_dimensions)
        img = Image.fromarray(new_cropped_image_array)
        scaled_image_array = self.threshold(np.asarray((img.resize((160, 45), Image.BILINEAR))))
        scaled_image = Image.fromarray(scaled_image_array)

        # save image
        path = "Debug"
        scaled_image.save(path + "\\" + mode + " scaled.png", "PNG")

        if len(scaled_image_array[0]) != len(self.gameEndReference["Victory"][0]) and \
                len(scaled_image_array) != len(self.gameEndReference["Victory"]):
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
        map_type = self.map_type()
        if map_type == "transition":
            if "currentType" in self.objectiveProgress:
                if self.objectiveProgress["currentType"] is None:
                    map_type = "assault"
                else:
                    map_type = self.objectiveProgress["currentType"]
            else:
                map_type = "assault"
        this_map = [
            self.currentMapSide,  # side options: offense, defense
            map_type,  # type options: escort, assault, control
            "single_hero"
        ]

        options_to_send = ["options", this_map]
        if broadcaster != "debug":
            broadcaster.publish(broadcaster.subscriptionString, options_to_send)

    def set_game_over(self):
        self.objectiveProgress["gameOver"] = True

    def get_current_map(self):
        map_name = ""
        for string in self.current_map:
            if string.isdigit():
                break
            else:
                map_name = map_name + string + "-"
        return map_name[:-1]

    def get_objective_progress(self):
        objective_dictionary = copy.deepcopy(self.objectiveProgress)
        del objective_dictionary["gameOver"]
        del objective_dictionary["gameEnd"]

        return objective_dictionary

    def dimensions_from_version(self):
        dimensions = {
            "1.16": {
                "assault": {
                    "point1": {
                        "start_x": 918,
                        "end_x": 930,
                        "start_y": 125,
                        "end_y": 139
                    },
                    "point2": {
                        "start_x": 994,
                        "end_x": 1006,
                        "start_y": 125,
                        "end_y": 139
                    },
                    "transition": {
                        "start_x": 760,
                        "end_x": 772,
                        "start_y": 125,
                        "end_y": 139
                    }
                },
                "control": {
                    "normal": {
                        'start_x': 952,
                        'end_x': 968,
                        'start_y': 78,
                        'end_y': 102
                    },
                    "locked": {
                        'start_x': 952,
                        'end_x': 968,
                        'start_y': 115,
                        'end_y': 139
                    },
                    "overtime": {
                        'start_x': 952,
                        'end_x': 968,
                        'start_y': 133,
                        'end_y': 157
                    }
                },
                "escort": {
                    "quick": {
                        "lock": {
                            "start_x": 953,
                            "end_x": 965,
                            "start_y": 110,
                            "end_y": 124
                        },
                        "progress_bar": {
                            "escort": {
                                "start_x": 787,
                                "end_x": 1135,
                                "start_y": 120,
                                "end_y": 130
                            },
                            "transition": {
                                "start_x": 824,
                                "end_x": 1172,
                                "start_y": 120,
                                "end_y": 130
                            }

                        },
                    },
                    'competitive': {
                        'lock': {
                            "start_x": 953,
                            "end_x": 965,
                            "start_y": 123,
                            "end_y": 137
                        },
                        "progress_bar": {
                            "escort": {
                                "start_x": 787,
                                "end_x": 1135,
                                "start_y": 132,
                                "end_y": 142
                            },
                            "transition": {
                                "start_x": 824,
                                "end_x": 1172,
                                "start_y": 132,
                                "end_y": 142
                            },
                        }

                    }
                },
                'competitive': {
                    'offense': {
                        'start_x': 760,
                        'end_x': 880,
                        'y': 84
                    }, 'defense': {
                        'start_x': 1030,
                        'end_x': 1180,
                        'y': 84
                    }
                },
                'game_end': {
                    'quick': {
                        'start_x': 730,
                        'end_x': 1200,
                        'start_y': 270,
                        'end_y': 410
                    },
                    'competitive': {
                        'start_x': 643,
                        'end_x': 1305,
                        'start_y': 440,
                        'end_y': 633
                    }
                }
            },
            "1.17": {
                "assault": {
                    "point1": {
                        "start_x": 918,
                        "end_x": 930,
                        "start_y": 125,
                        "end_y": 139
                    },
                    "point2": {
                        "start_x": 994,
                        "end_x": 1006,
                        "start_y": 125,
                        "end_y": 139
                    },
                    "transition": {
                        "start_x": 760,
                        "end_x": 772,
                        "start_y": 125,
                        "end_y": 139
                    }
                },
                "control": {
                    "normal": {
                        'start_x': 952,
                        'end_x': 968,
                        'start_y': 87,
                        'end_y': 111
                    },
                    "locked": {
                        'start_x': 952,
                        'end_x': 968,
                        'start_y': 138,
                        'end_y': 162
                    },
                    "overtime": {
                        'start_x': 952,
                        'end_x': 968,
                        'start_y': 147,
                        'end_y': 171
                    }
                },
                "escort": {
                    "quick": {
                        "lock": {
                            "start_x": 953,
                            "end_x": 965,
                            "start_y": 110,
                            "end_y": 124
                        },
                        "progress_bar": {
                            "escort": {
                                "start_x": 787,
                                "end_x": 1135,
                                "start_y": 120,
                                "end_y": 130
                            },
                            "transition": {
                                "start_x": 824,
                                "end_x": 1172,
                                "start_y": 120,
                                "end_y": 130
                            }

                        },
                    },
                    'competitive': {
                        'lock': {
                            "start_x": 953,
                            "end_x": 965,
                            "start_y": 123,
                            "end_y": 137
                        },
                        "progress_bar": {
                            "escort": {
                                "start_x": 787,
                                "end_x": 1135,
                                "start_y": 132,
                                "end_y": 142
                            },
                            "transition": {
                                "start_x": 824,
                                "end_x": 1172,
                                "start_y": 132,
                                "end_y": 142
                            },
                        }

                    }
                },
                'competitive': {
                    'offense': {
                        'start_x': 760,
                        'end_x': 880,
                        'y': 84
                    }, 'defense': {
                        'start_x': 1030,
                        'end_x': 1180,
                        'y': 84
                    }
                },
                'game_end': {
                    'quick': {
                        'start_x': 730,
                        'end_x': 1200,
                        'start_y': 270,
                        'end_y': 410
                    },
                    'competitive': {
                        'start_x': 643,
                        'end_x': 1305,
                        'start_y': 440,
                        'end_y': 633
                    }
                }
            }
        }
        return dimensions[self.game_version]
