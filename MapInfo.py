from PIL import Image, ImageFilter, ImageOps
import numpy as np
from scipy.misc import imresize
import operator
import copy

from MapState import MapState

from GameObject import GameObject


class MapInfo(GameObject):

    def __init__(self, game_version, debug_mode):
        self.game_version = game_version
        self.debugMode = debug_mode

        self.mapDictionary = {
            # assault
            "hanamura": "assault", "horizon lunar colony": "assault", "temple of anubis": "assault",
            "volskaya industries": "assault",
            # transition
            "blizzard world": "transition", "eichenwalde": "transition", "hollywood": "transition",
            "king's row": "transition", "numbani": "transition",
            # control
            "ilios": "control", "lijiang tower": "control", "nepal": "control", "oasis": "control",
            # escort
            "dorado": "escort", "junkertown": "escort", "rialto": "escort", "route 66": "escort",
            "watchpoint gibraltar": "escort",
            # arena
            "ayutthaya": "arena", "black forest": "arena", "castillo": "arena", "chateau guillard": "arena",
            "ecopoint antarctica": "arena", "ilios lighthouse": "arena", "ilios ruins": "arena", "ilios well": "arena",
            "lijiang control center": "arena", "lijiang garden": "arena", "lijiang night market": "arena",
            "necropolis": "arena", "nepal sanctum": "arena", "nepal shrine": "arena", "nepal village": "arena",
            "oasis city center": "arena", "oasis gardens": "arena", "oasis university": "arena", "petra": "arena",
        }
        self.mapReferences = {
            "Hero Select Assault": self.read_references("Reference\\MapImageListAssault.txt"),
            "Hero Select Control": self.read_references("Reference\\MapImageListControl.txt"),
            "Hero Select Escort": self.read_references("Reference\\MapImageListEscort.txt"),
            "Hero Select Hybrid": self.read_references("Reference\\MapImageListHybrid.txt"),
            "Hero Select Arena": self.read_references("Reference\\MapImageListArena.txt"),
            "Tab": self.read_references("Reference\\MapImageListTab.txt"),
            # "High Threshold": self.read_references("Reference\\MapImageHighThreshold.txt"),
            "Game Type": self.read_references("Reference\\MapImageListGameType.txt"),
            "Letters": self.read_references("Reference\\Letters.txt"),
        }
        self.assaultReference = self.read_references("Reference\\ObjectiveListAssault.txt")
        self.controlReference = self.read_references("Reference\\ObjectiveListControl.txt")
        full_digit_references = self.read_references("Reference\\DigitImageList.txt")
        self.digitReferences = {new_key: full_digit_references[new_key] for new_key in {"0", "1", "2"}}
        self.gameEndReference = self.read_references("Reference\\GameEnd.txt")

        self.imageThreshold = {
            "Hero Select": 0.87,
            "Tab": 0.9,
            "Assault": 0.88,
            "Control": 0.88,
            "Victory": 0.88,
            "Defeat": 0.88,
            "Game Type": 0.855
        }

        self.current_map_state = MapState()
        self.previous_map_state = MapState()
        self.current_map = [None]
        self.currentMapSide = "offense"
        self.mapChange = False
        self.map_transitioned = False  # for broadcasting new map type

        self.previousMap = [None]
        self.previousMapSide = None

        self.currentImageArray = None
        self.potential = None
        self.thisMapPotential = None
        self.previousImageArray = None
        self.previousPotential = None

        self.game_mode = None
        self.previous_game_mode = None

        self.competitive = True
        self.competitive_confirmed = False
        self.check_competitive = True

        self.objectiveProgress = {}
        self.assaultPixelsToCheck = []

        self.letters_rle = {}
        for letter, image in self.mapReferences["Letters"].items():
            self.letters_rle[letter] = self.run_length_encode(image)

        self.dimensions = self.dimensions_from_version()
        self.calculate_assault_progress_pixels()

    def main(self, screen_image_array, current_time):
        """Process the saved screen shot to see what the current view is (either "Tab" or "Hero Select")

        :param: screen_image_array: Numpy array of the screen shot
        :param: current_time: String of the current time
        :return: string (view) if found, or boolean (False)
        """
        # check if Tab View
        map_result = self.identify_map(screen_image_array, "Tab", current_time)
        if map_result:
            this_view = "Tab"
            self.check_competitive = True
        else:
            # check if Hero Select View
            map_result = self.identify_map(screen_image_array, "Hero Select", current_time)
            if map_result:
                this_view = "Hero Select"
                self.check_competitive = True
            else:
                this_view = False
        return this_view

    def reset_objective_progress(self):
        """Sets variables involved in tracking each teams's objective progress to defaults.

        :return: None
        """
        self.competitive = True
        self.competitive_confirmed = False
        self.check_competitive = True

        self.objectiveProgress = {
            "currentType": None,
            "gameEnd": False,
            "gameOver": False,
            "unlocked": False
        }

        map_type = self.map_type()
        if map_type == "assault" or map_type == "transition":
            self.objectiveProgress["assaultPoint"] = False
            self.objectiveProgress["assaultPointProgress"] = None
        if map_type == "control":
            self.objectiveProgress["controlProgress"] = [None, None, None, None]
        if map_type == "escort" or map_type == "transition":
            self.objectiveProgress["escortProgress"] = []

    def calculate_assault_progress_pixels(self):
        """ Progress on each assault point is displayed with a radial bar that fills as the team captures the point.
        This calculates the pixels to check based on each point's center.

        :return: None
        """
        assault_radius = 23  # px
        self.assaultPixelsToCheck = {}
        for map_type in ["assault", "transition"]:
            self.assaultPixelsToCheck[map_type] = {}
            for mode in ["quick", "competitive"]:
                center_points = [
                    [
                        self.dimensions[map_type][mode]["point1"]["start_x"] + 6,
                        self.dimensions[map_type][mode]["point1"]["start_y"] + 6
                    ]
                ]
                if map_type == "assault":
                    center_points.append([
                        self.dimensions[map_type][mode]["point2"]["start_x"] + 6,
                        self.dimensions[map_type][mode]["point2"]["start_y"] + 6
                    ]
                    )
                point_number = 0
                self.assaultPixelsToCheck[map_type][mode] = []
                for centerPoint in center_points:
                    self.assaultPixelsToCheck[map_type][mode].append([])
                    for percentage in range(1, 101):
                        # theta = -(percentage - 125) / (5 / 18) # complete circle; it is segmented as of patch 1.17
                        if 1 <= percentage <= 33:
                            theta = 108.23 * percentage / -32 + 448.41
                        elif 34 <= percentage <= 66:
                            theta = 108.62 * percentage / -32 + 440.42
                        elif 67 <= percentage <= 100:
                            theta = 108.23 * percentage / -33 + 422.94

                        x_coordinate = int((np.cos(np.deg2rad(theta)) * assault_radius) + centerPoint[0])
                        if percentage < 50:  # center isn't perfectly center
                            x_coordinate = x_coordinate + 1
                        y_coordinate = int(-(np.sin(np.deg2rad(theta)) * assault_radius) + centerPoint[1])
                        if 25 < percentage < 75:  # center isn't perfectly center
                            y_coordinate = y_coordinate + 1
                        # print(str(percentage) + " " + str(theta) + " " + str(x_coordinate) + " " + str(y_coordinate))
                        self.assaultPixelsToCheck[map_type][mode][point_number].append([x_coordinate, y_coordinate])
                    point_number = point_number + 1

    def map_type(self):
        """ Returns the current map type, defaulting to assault

        :return: String (map type)
        """
        if self.current_map[0] is None:
            return "assault"
        else:
            return self.mapDictionary[self.current_map[0]]

    def identify_map(self, screen_img_array, view, current_time):
        """ Processes the screen shot to see if we are in a requested view.

        :param screen_img_array: Numpy array of the screen shot
        :param view: String of view to check
        :param: current_time: String of the current time
        :return: Boolean if map (and thus view) is identified
        """
        potential = None
        section = "normal"

        if view == "Hero Select":
            game_mode_identified = self.identify_game_type(screen_img_array, view)
            if game_mode_identified:
                # The game mode is an icon to the left of the map's name, causing that name to be pushed to the right
                section = "extended"

        this_map_array = self.get_map(screen_img_array, view, section=section)
        map_reference = self.what_map_reference(view, section)
        potential = self.what_image_is_this(this_map_array, map_reference)
        this_map = max(potential.keys(), key=(lambda k: potential[k]))

        self.previousImageArray = self.currentImageArray
        self.currentImageArray = this_map_array
        self.previousPotential = self.potential
        self.potential = potential
        self.thisMapPotential = potential[this_map]
        if potential[this_map] > self.imageThreshold[view]:
            if self.debugMode:
                print(str(potential[this_map]) + " " + this_map)

            this_map_split = this_map.split("-")
            if self.current_map[0] != this_map_split[0]:
                print("Map Changed")
                self.mapChange = True
            else:
                self.mapChange = False
            self.previousMap = self.current_map
            self.current_map = this_map_split
            return True
        elif section == "extended" and self.debugMode:
            self.save_debug_data(section, current_time)
        # elif view == "Hero Select":
        #     # Some maps have a mostly white cloud background that moves
        #     this_map_array = self.get_map(screen_img_array, view, section=section, threshold_balance=True)
        #     potential = self.what_image_is_this(this_map_array, self.mapReferences["High Threshold"])
        #     this_map = max(potential.keys(), key=(lambda k: potential[k]))
        #     if potential[this_map] > self.imageThreshold[view]:
        #         this_map_split = this_map.split("-")
        #         if self.current_map[0] != this_map_split[0]:
        #             print("Map Changed")
        #             self.mapChange = True
        #         else:
        #             self.mapChange = False
        #         self.previousMap = self.current_map
        #         self.current_map = this_map_split
        #         print(this_map)
        #         return True
        #     else:
        #         return False
        else:
            return False

    def identify_game_type(self, screen_img_array, view):
        """ Processes the screen shot to see if we can identify the game type.

        :param screen_img_array: Numpy array of the screen shot
        :param view: String of view to check
        :return: Boolean if game type is identified
        """
        this_mode_array = self.get_map(screen_img_array, view, section='game_type')
        # img = Image.fromarray(this_mode_array)
        # img.save("Debug\\Game Mode.png", "PNG")
        potential = self.what_image_is_this(this_mode_array, self.mapReferences['Game Type'])
        this_game_mode = max(potential.keys(), key=(lambda k: potential[k]))
        if potential[this_game_mode] > self.imageThreshold["Game Type"]:
            self.previous_game_mode = self.game_mode
            this_game_mode_split = this_game_mode.split("-")
            self.game_mode = this_game_mode_split[0]
            print(this_game_mode + " " + str(potential[this_game_mode]))
            #  Hero Select Confirmed
            return True
        else:
            return False

    def what_map_reference(self, view, section):
        """ Returns a portion of the maps to check

        :param view: String
        :param section: String
        :return: Dictionary of the maps to check
        """
        if view == "Tab":
            map_reference = self.mapReferences["Tab"]
        elif section == "normal":
            map_reference = self.mapReferences["Hero Select Assault"]
        else:
            if self.game_mode == "control":
                map_reference = self.mapReferences["Hero Select Control"]
            elif self.game_mode == "escort":
                map_reference = self.mapReferences["Hero Select Escort"]
            elif self.game_mode == "transition":
                map_reference = self.mapReferences["Hero Select Hybrid"]
            else:
                map_reference = self.mapReferences["Hero Select Arena"]
        return map_reference

    def save_debug_data(self, section, current_time, current_image_array=None, potential=None):
        """ Saves the current map to the Debug Folder

        :param section: String of the current date and time
        :param current_time: String of the current date and time
        :param current_image_array: Image array to be saved
        :param potential: array of potential maps to be saved
        :return: None
        """

        if current_image_array is None:
            current_image_array = self.currentImageArray

        if potential is None:
            potential = self.potential

        # save image
        img = Image.fromarray(current_image_array)
        img.save("Debug\\Potential " + section + " " + current_time + " map.png", "PNG")

        # save potential
        debug_file = open("Debug\\Potential " + section + " " + current_time + " map.txt", 'w')
        for potentialMap, value in sorted(potential.items(), key=operator.itemgetter(1), reverse=True):
            line_to_write = str(value) + ': ' + potentialMap + '\n'
            debug_file.write(line_to_write)

    def get_map(self, img_array, view, section='normal', threshold_balance=False):
        """ Processes the screen shot to pull out the desired section and filter it

        :param img_array: Numpy array of the screen shot
        :param view: String of the requested view
        :param section: String of the specific section of the screen shot requested
        :param threshold_balance: Boolean if we want to calculated the threshold or not
        :return: Numpy array of processed screen shot
        """
        scaled_image_array = None

        dimensions = self.dimensions['map'][view][section]

        map_image = img_array[dimensions['start_y']:dimensions['end_y'], dimensions['start_x']:dimensions['end_x']]
        map_image_array = np.asarray(map_image)

        if view == "Hero Select":
            if section != 'game_type':
                # img = Image.fromarray(map_image_array)
                # img.save("Debug\\Full Original Map.png", "PNG")
                processed_image_array = self.process_image(map_image_array, filter_enabled=True)
                scaled_image_array = imresize(processed_image_array, (19, 180))
            else:
                scaled_image_array = self.process_image(map_image_array, filter_enabled=True)
        elif view == "Tab":
            scaled_image_array = map_image_array

        if not threshold_balance:
            new_image_array = self.threshold(scaled_image_array)
        else:
            new_image_array = self.image_to_black_and_white(scaled_image_array, 252)

        return new_image_array

    @staticmethod
    def process_image(map_image_array, filter_enabled=True):
        """ Applies filters and clears edges on provided image array

        :param map_image_array: Numpy array of the image to be filtered
        :param filter_enabled: Boolean to apply filters
        :return: Numpy array of processed image
        """

        # straighten letters
        # flipped = np.flipud(map_image_array)
        # flipped.setflags(write=True)
        # for row_number, row in enumerate(flipped):
        #     left_shift = int(row_number / 3.72)  # 41 / 11
        #     if left_shift > 0:
        #         for column_number, pixel in enumerate(row):
        #             try:
        #                 flipped[row_number][column_number] = flipped[row_number][column_number + left_shift]
        #             except IndexError:
        #                 flipped[row_number][column_number] = 0
        # map_image_array = np.flipud(flipped)

        if filter_enabled:
            map_image = Image.fromarray(map_image_array)
            contoured_image = map_image.filter(ImageFilter.CONTOUR)  # .filter(ImageFilter.SMOOTH_MORE)
            inverted_image = ImageOps.invert(contoured_image)

            img_array = np.asarray(inverted_image)
            img_array.setflags(write=True)
            for row_number, row in enumerate(img_array):
                for column_number, column in enumerate(row):
                    first_four_rows = list(range(0, 4))
                    last_four_rows = list(range(len(img_array) - 4, len(img_array)))
                    if row_number in first_four_rows or row_number in last_four_rows:
                        img_array[row_number][column_number] = [0, 0, 0]
                    elif column_number == 0 or column_number == len(column):
                        img_array[row_number][column_number] = [0, 0, 0]
        else:
            img_array = map_image_array

        return img_array

    def identify_side(self, img_array):
        """ Processes the image to identifies your team's side

        :param img_array: Numpy array of the image to check
        :return: Boolean if side identified
        """
        pixel_to_check = img_array[79][95]
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
    def team_from_pixel(pixel_to_check, opposite=False):
        """ Identifies a team's side based on the color at a specific pixel

        :param pixel_to_check: Array of the pixel to check
        :param opposite: Boolean to switch the results
        :return: String of side identified
        """

        red = pixel_to_check[0]
        green = pixel_to_check[1]
        blue = pixel_to_check[2]

        if (red > 195) and (green < 200) and (blue < 200):  # red
            this_side = "offense"
        elif (red < 200) and (green > 170) and (blue > 100):  # blue
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

    @staticmethod
    def team_from_pixel_assault_circle(pixel_to_check, opposite=False):
        """ Identifies a team's side based on the color at a specific pixel in the objective icon

        :param pixel_to_check: Array of the pixel to check
        :param opposite: Boolean to switch the results
        :return: String of side identified
        """
        red = pixel_to_check[0]
        green = pixel_to_check[1]
        blue = pixel_to_check[2]

        if red > 245 and green < 230 and blue < 240:
            this_side = "offense"
        elif (blue > 230 and green > 170 and red < 205 and int(green) - int(red) > 40) or \
                (red >= 245 and green >= 250 and blue >= 250):
            # blue/teal or white
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

    @staticmethod
    def team_from_pixel_precise(pixel_to_check, opposite=False):
        """ Identifies a team's side based on the color at a specific pixel.
        This function also checks ranges between colors

        :param pixel_to_check: Array of the pixel to check
        :param opposite: Boolean to switch the results
        :return: String of side identified
        """
        red = pixel_to_check[0]
        green = pixel_to_check[1]
        blue = pixel_to_check[2]
        # print(red)
        # print(green)
        # print(blue)
        if (175 <= red <= 255) and (0 <= green <= 200) and (0 <= blue <= 200) \
                and (int(red) - int(blue) > 10) and (int(red) - int(green) > 10):
            this_side = "offense"
        elif (38 <= red <= 215) and (140 <= green <= 255) and (175 <= blue <= 255) and (int(blue) - int(red) > 10):
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

    def identify_objective_progress(self, img_array, mode="standard", current_view=False):
        """ Identifies the objective progress based on the screen shot

        :param img_array: Numpy Array of screen shot
        :param mode: String, used for specifying debugging or saving for reference
        :param current_view: Boolean or String, String is of the view identified when detecting the map
        :return: Boolean if identification was attempted
        """
        if "gameOver" not in self.objectiveProgress:
            return False
        if self.current_map == [None] or self.objectiveProgress["gameOver"] is True:
            return False
        map_type = self.map_type()
        new_image_array = None
        self.map_transitioned = False

        if map_type == "transition":
            # need to go from assault to escort
            if self.objectiveProgress["currentType"] is None:
                self.objectiveProgress["currentType"] = "assault"
        else:
            self.objectiveProgress["currentType"] = map_type

        if self.objectiveProgress["currentType"] == "assault":
            new_image_array = self.identify_assault_objective_progress(img_array, map_type, current_view, mode)

        if self.objectiveProgress["currentType"] == "control":
            new_image_array = self.identify_control_objective_progress(img_array, mode)

        if self.objectiveProgress["currentType"] == "escort":
            new_image_array = self.identify_escort_objective_progress(img_array, map_type, current_view, mode)

        if mode == "for_reference" and new_image_array is not None:
            # save image
            img = Image.fromarray(new_image_array)
            img.save("Debug\\Potential Objective.png", "PNG")

        return True

    def identify_assault_objective_progress(self, img_array, map_type, current_view, mode="standard", loop_count=0):
        """ Identifies the assault objective progress based on the screen shot

        :param img_array: Numpy Array of screen shot
        :param map_type: String of map type to be used for cropping dimensions
        :param current_view: Boolean or String, String is of the view identified when detecting the map
        :param mode: String, used for specifying debugging or saving for reference
        :param loop_count: Integer of how many times this function has called itself
        :return: None if transitioning, Numpy array of objective UI otherwise
        """

        # The only time to check if this is a competitive mode is immediately after a tab view
        if self.check_competitive and current_view != "Tab":
            self.competitive = self.identify_competitive(img_array, mode)
            self.check_competitive = False
            print("Competitive: " + str(self.competitive))

        competitive_string = self.get_competitive_string()

        check_game_end = True
        new_image_array = None
        this_status = None
        potential = None

        if self.objectiveProgress["assaultPoint"] == "B":
            check_assault_point2 = True
        else:
            check_assault_point2 = False

        if self.objectiveProgress["assaultPoint"] != "B":
            # Assault Point 1

            dimensions = self.dimensions[map_type][competitive_string]["point1"]
            new_image_array = self.cut_and_threshold(
                img_array, dimensions)
            potential = self.what_image_is_this(new_image_array, self.assaultReference)
            this_status = max(potential.keys(), key=(lambda k: potential[k]))

            if self.debugMode:
                # save image
                img = Image.fromarray(new_image_array)
                img.save("Debug\\Potential Assault Point 1 " + str(loop_count) + ".png", "PNG")

            if potential[this_status] > self.imageThreshold["Assault"]:
                check_game_end = False
                self.competitive_confirmed = True
                this_status_split = this_status.split("-")
                this_status = this_status_split[0]
                if this_status == "Done":
                    if map_type == "transition":
                        print("Transition to Escort")
                        self.objectiveProgress["currentType"] = "escort"
                        self.map_transitioned = True
                        return  # will now enter identify_escort_objective_progress
                    else:
                        check_assault_point2 = True
                elif this_status != "Locked":
                    self.objectiveProgress["unlocked"] = True
                    self.identify_assault_point_progress(img_array, map_type, competitive_string, 0, mode)
                else:
                    check_assault_point2 = True
            elif map_type == "transition":
                new_image_array = self.cut_and_threshold(
                    img_array, self.dimensions[map_type][competitive_string]["done"])
                potential = self.what_image_is_this(new_image_array, self.assaultReference)
                this_status_key = max(potential.keys(), key=(lambda k: potential[k]))
                this_status_split = this_status_key.split("-")
                this_status = this_status_split[0]
                if potential[this_status_key] > self.imageThreshold["Assault"] and \
                        (this_status == "Locked" or this_status == "Done"):
                    self.competitive_confirmed = True
                    print("Transition to Escort")
                    self.objectiveProgress["currentType"] = "escort"
                    self.map_transitioned = True
                    return  # will now enter identify_escort_objective_progress
                else:
                    check_game_end = True
        if check_assault_point2:
            # Assault Point 2
            new_image_array = self.cut_and_threshold(
                img_array, self.dimensions["assault"][competitive_string]["point2"])
            potential = self.what_image_is_this(new_image_array, self.assaultReference)
            this_status_not_split = max(potential.keys(), key=(lambda k: potential[k]))
            this_status_split = this_status_not_split.split("-")
            this_status = this_status_split[0]

            if self.debugMode:
                # save image
                img = Image.fromarray(new_image_array)
                img.save("Debug\\Potential Assault Point 2 " + str(loop_count) + ".png", "PNG")

            if potential[this_status_not_split] > self.imageThreshold["Assault"]:
                check_game_end = False
                self.competitive_confirmed = True
                if this_status != "Locked":
                    self.objectiveProgress["unlocked"] = True
                    self.identify_assault_point_progress(img_array, map_type, competitive_string, 1, mode)
                else:
                    self.objectiveProgress["unlocked"] = False
        if check_game_end:
            if not self.competitive_confirmed and loop_count == 0:
                self.competitive = not self.competitive
                print("Try Competitive: " + str(self.competitive))
                new_image_array = self.identify_assault_objective_progress(
                    img_array, map_type, current_view, mode, loop_count=1)
            else:
                if loop_count == 1:
                    self.competitive = not self.competitive
                self.identify_game_end(img_array, mode)
        else:
            if this_status != self.objectiveProgress["assaultPoint"]:
                self.objectiveProgress["assaultPoint"] = this_status
                print(this_status)
                print(potential)

        return new_image_array

    def identify_assault_point_progress(self, img_array, map_type, competitive_string, point_number, mode="standard"):
        """ Identifies the assault objective progress based on the screen shot

        :param img_array: Numpy Array of screen shot
        :param map_type: String of map type to be used for cropping dimensions
        :param competitive_string: String of whether the mode is competitive
        :param point_number: Int of point to check
        :param mode: String, used for specifying debugging or saving for reference
        :return: None
        """

        assault_percent_complete = 0
        img_copy = img_array.copy()
        img_copy.setflags(write=1)
        fail_count = 0
        for percent, pixelCoordinates in \
                enumerate(self.assaultPixelsToCheck[map_type][competitive_string][point_number]):
            x_coordinate = pixelCoordinates[0]
            y_coordinate = pixelCoordinates[1]
            this_pixel = img_array[y_coordinate][x_coordinate]
            debug_color = 0
            pixel_side = self.team_from_pixel_assault_circle(this_pixel, opposite=True)
            assault_percent_complete = assault_percent_complete + 1
            if self.currentMapSide == pixel_side:
                debug_color = 255
                fail_count = 0
            else:
                fail_count += 1
                if fail_count == 10 or percent == 100:
                    assault_percent_complete -= fail_count
                    break

            if mode != "standard":
                print(str(percent) + " " + str(self.currentMapSide == pixel_side) + " " +
                      str([x_coordinate, y_coordinate]) + str(this_pixel))

            img_copy[y_coordinate][x_coordinate][0] = debug_color
            img_copy[y_coordinate][x_coordinate][1] = debug_color
            img_copy[y_coordinate][x_coordinate][2] = debug_color

        self.objectiveProgress["assaultPointProgress"] = assault_percent_complete
        print("Percent Complete: " + str(assault_percent_complete))
        if self.debugMode:
            img = Image.fromarray(img_copy)
            img.save("Debug\\Assault Progress.png", "PNG")

    def identify_control_objective_progress(self, img_array, mode="standard"):
        """ Identifies the control objective progress based on the screen shot

        :param img_array: Numpy Array of screen shot
        :param mode: String, used for specifying debugging or saving for reference
        :return: Numpy array of objective UI
        """

        pixel_current_height = 118
        pixel_side_height = 91
        reference = self.controlReference
        status_addendum = ""
        objective_image_array = self.cut_and_threshold(img_array, self.dimensions["control"]["normal"])
        objective_identified = self.identify_control_core(img_array, objective_image_array, pixel_current_height,
                                                          pixel_side_height, reference, status_addendum)
        self.objectiveProgress["unlocked"] = True

        if objective_identified is False:
            # check if not controlled with a black background
            inverted_objective_image_array = self.invert_image_array(objective_image_array)
            objective_identified = self.identify_control_core(img_array, inverted_objective_image_array,
                                                              pixel_current_height, pixel_side_height, reference,
                                                              status_addendum)

        if objective_identified is False:
            # check if locked between rounds
            pixel_current_height = 145
            pixel_side_height = 128
            reference = {"Prepare": self.controlReference["Locked"]}
            status_addendum = ""
            objective_image_array = self.cut_and_threshold(img_array, self.dimensions["control"]["locked"])
            inverted_objective_image_array = self.invert_image_array(objective_image_array)
            objective_identified = self.identify_control_core(img_array, inverted_objective_image_array,
                                                              pixel_current_height, pixel_side_height, reference,
                                                              status_addendum)
        if objective_identified is False:
            # check for overtime
            pixel_current_height = 163
            pixel_side_height = 146
            reference = self.controlReference
            status_addendum = "-Overtime"
            objective_image_array = self.cut_and_threshold(img_array, self.dimensions["control"]["overtime"])
            objective_identified = self.identify_control_core(img_array, objective_image_array, pixel_current_height,
                                                              pixel_side_height, reference, status_addendum)
        if objective_identified is False:
            self.identify_game_end(img_array, mode)
        else:
            self.objectiveProgress["unlocked"] = False

        return objective_image_array

    def identify_control_core(self, full_screen_img_array, objective_image_array, pixel_current_height,
                              pixel_side_height, reference, status_addendum):
        """ Attempts to identify the control objective progress

        :param full_screen_img_array: Numpy Array of screen shot
        :param objective_image_array: Numpy Array of potential objective to check
        :param pixel_current_height: Int of pixel's y value to find objective's current controlling team
        :param pixel_side_height: Int of pixel's y value to find number of rounds won
        :param reference: Dictionary of images to check
        :param status_addendum: String, used for elaborating on the current status e.g. overtime
        :return: Boolean of successfully identifying objective
        """

        this_side = "neither"

        competitive_progress = False
        our_progress = 0
        their_progress = 0

        potential = self.what_image_is_this(objective_image_array, reference)
        this_status = max(potential.keys(), key=(lambda k: potential[k]))

        successfully_identified = potential[this_status] > self.imageThreshold["Control"]

        if successfully_identified:
            pixel_to_check = {
                'current': full_screen_img_array[pixel_current_height][959],
                'left': {
                    0: full_screen_img_array[pixel_side_height][774],
                    1: full_screen_img_array[pixel_side_height][814]
                },
                'right': {
                    0: full_screen_img_array[pixel_side_height][1146],
                    1: full_screen_img_array[pixel_side_height][1106]
                }
            }
            if this_status not in ["Locked", "Prepare"]:
                this_side = self.team_from_pixel(pixel_to_check["current"])
                print("Current Controller: " + this_side)

            if (self.objectiveProgress["controlProgress"][1] is None and this_status != "Prepare")\
                    or this_status == "Locked":
                competitive_progress = self.identify_control_competitive_progress(full_screen_img_array)

            if self.competitive and competitive_progress is not False:
                our_progress = competitive_progress[0]
                their_progress = competitive_progress[1]
            elif self.competitive:
                our_progress = self.objectiveProgress["controlProgress"][1]
                their_progress = self.objectiveProgress["controlProgress"][2]
            else:
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
            if self.objectiveProgress["controlProgress"][1] != our_progress\
                    or self.objectiveProgress["controlProgress"][2] != their_progress:
                print("Game Progress | Us: " + str(our_progress) + "   Them: " + str(their_progress))

            this_status = this_status + status_addendum
            if this_status != self.objectiveProgress["controlProgress"][0]:
                print(this_status)
            self.objectiveProgress["controlProgress"] = [this_status, our_progress, their_progress, this_side]
            return True
        else:
            return False

    def identify_control_competitive_progress(self, img_array, mode="standard"):
        """ Identifies the competitive control objective progress based on the screen shot
        Competitive is unique in that the number of rounds won is displayed with digits

        :param img_array: Numpy Array of screen shot
        :param mode: String, used for specifying debugging or saving for reference
        :return: Boolean of successfully identifying objective
        """

        offense_found, offense_result = self.identify_control_competitive_side_progress(img_array, "offense", mode)
        defense_found, defense_result = self.identify_control_competitive_side_progress(img_array, "defense", mode)

        self.check_competitive = False
        self.competitive_confirmed = True
        if offense_found and defense_found:
            # print("Competitive")
            self.competitive = True
            return [offense_result, defense_result]
        else:
            # print("Not Competitive")
            return False

    def identify_control_competitive_side_progress(self, img_array, team_side, mode="standard"):
        """ Identifies a specific team's competitive control objective progress based on the screen shot
        Competitive is unique in that the number of rounds won is displayed with digits

        :param img_array: Numpy Array of screen shot
        :param team_side: String of which team to check
        :param mode: String, used for specifying debugging or saving for reference
        :return: Boolean of successfully identifying objective
        """
        dimensions = self.dimensions["control"]["competitive"][team_side + "_score"]
        new_image_array = self.cut_image(img_array, dimensions)
        img = Image.fromarray(new_image_array)
        scaled_image_array = self.threshold(np.asarray((img.resize((8, 11), Image.BILINEAR))))

        if self.debugMode:
            # save image
            img = Image.fromarray(scaled_image_array)
            img.save("Debug\\Potential Competitive " + team_side + " Score.png", "PNG")

        potential = self.what_image_is_this(scaled_image_array, self.digitReferences)
        this_status = max(potential.keys(), key=(lambda k: potential[k]))
        # print(potential[this_status])
        if potential[this_status] > 70:
            # print(team_side + " score: " + this_status)
            return True, this_status
        else:
            return False, False

    def identify_escort_objective_progress(self, img_array, map_type, current_view, mode="standard"):
        """ Identifies the escort objective progress based on the screen shot

        :param img_array: Numpy Array of screen shot
        :param map_type: String of map type to be used for cropping dimensions
        :param current_view: Boolean or String, String is of the view identified when detecting the map
        :param mode: String, used for specifying debugging or saving for reference
        :return: Numpy array of objective UI
        """
        if self.check_competitive and current_view != "Tab":
            self.competitive = self.identify_competitive(img_array, mode)
            self.check_competitive = False
            print("Competitive: " + str(self.competitive))

        competitive_string = self.get_competitive_string()

        if map_type == "escort" and self.objectiveProgress["unlocked"] is False:
            # check for lock symbol

            new_image_array = self.cut_and_threshold(img_array, self.dimensions["escort"][competitive_string]["lock"])
            lock_reference = {
                "Locked": self.assaultReference["Locked-Thick"]
            }
            potential = self.what_image_is_this(new_image_array, lock_reference)

            if mode == "for_reference":
                # save image
                img = Image.fromarray(new_image_array)
                img.save("Debug\\Potential Locked Objective.png", "PNG")

            if potential["Locked"] > self.imageThreshold["Assault"]:
                print("Locked")
                # print(potential)

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
        # junkertown point 1: 32%
        # junkertown point 2: 64%

        new_image_array = self.cut_image(img_array,
                                         self.dimensions[map_type][competitive_string]["progress_bar"])
        end_found = False
        percent_complete = None

        dimensions = self.dimensions[map_type][competitive_string]["progress_bar"]

        for X in range(0, (dimensions["end_x"] - dimensions["start_x"])):
            pixel_to_check = new_image_array[5][X]
            pixel_team = self.team_from_pixel(pixel_to_check, opposite=True)
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

    @staticmethod
    def invert_image_array(image_array):
        new_array = image_array.copy()
        new_array.setflags(write=1)
        for row_index, row in enumerate(image_array):
            for pixel_index, pixel in enumerate(row):
                if pixel[0] == 0:
                    new_array[row_index][pixel_index] = [255, 255, 255]
                else:
                    new_array[row_index][pixel_index] = [0, 0, 0]
        return new_array

    def get_competitive_string(self):
        """ Returns either "competitive" or "quick" based on competitive boolean

        :return: String
        """
        if self.competitive:
            return "competitive"
        else:
            return "quick"

    def identify_competitive(self, img_array, mode="standard"):
        """ Identifies if the current mode is competitive or not

        :param img_array: Numpy Array of screen shot
        :param mode: String, used for specifying debugging or saving for reference
        :return: Boolean if competitive successfully identified
        """

        # check to see if there is a red or blue box (depending on team)
        box_beginning = 0
        box_end = 0
        x_coordinate = 0
        team_side = self.currentMapSide
        for x_coordinate in range(self.dimensions["competitive"][team_side]["start_x"],
                       self.dimensions["competitive"][team_side]["end_x"]):
            pixel_to_check = img_array[self.dimensions["competitive"][team_side]["y"]][x_coordinate]
            pixel_side = self.team_from_pixel_precise(pixel_to_check, opposite=True)
            if mode == "for_reference":
                print(str(x_coordinate) + " " + str(pixel_to_check) + " " + pixel_side)
            if pixel_side == team_side and box_beginning == 0:
                box_beginning = x_coordinate
            elif pixel_side == "neither" and box_beginning != 0 and box_end == 0:
                if 45 <= (x_coordinate - box_beginning) <= 124:
                    # Approximate size of box, may be larger when in bright light
                    if mode == "for_reference":
                        box_end = x_coordinate
                        print(str(box_beginning) + " " + str(box_end))
                    return True
                else:
                    box_beginning = 0
        # if it reaches the end of the for loop and is still the right color:
        if box_beginning != 0 and box_end == 0 and (45 <= (x_coordinate - box_beginning) <= 124):
            if mode == "for_reference":
                box_end = x_coordinate
                print(str(box_beginning) + " " + str(box_end))
            return True
        return False

    def identify_game_end(self, img_array, mode="standard"):
        """ Identifies if the game is over by checking for "Victory" or "Defeat"

        :param img_array: Numpy Array of screen shot
        :param mode: String, used for specifying debugging or saving for reference
        :return: None
        """

        print("Identify Game End")
        competitive_string = self.get_competitive_string()
        cropped_image_array = self.cut_image(img_array, self.dimensions["game_end"][competitive_string])

        if mode == "for_reference":
            # save image
            img = Image.fromarray(cropped_image_array)
            img.save("Debug\\" + "Game End Cropped.png", "PNG")

        # -- Check for Victory  -- #
        # convert to black and white based on yellow
        yellow = [230, 205, 141]
        result = self.game_end_format_image(cropped_image_array, yellow, "Victory")
        if type(result) is not bool:
            reference_dictionary = {
                'Victory': self.gameEndReference["Victory"]
            }
            potential = self.what_image_is_this(np.asarray(result), reference_dictionary)
            print('Victory Potential: ' + str(potential["Victory"]))
            if potential["Victory"] > self.imageThreshold["Victory"]:
                self.objectiveProgress["gameEnd"] = "Victory"
                print("Victory!")
                self.set_game_over()
        if self.objectiveProgress["gameEnd"] != "Victory":
            # -- Check for Defeat -- #
            red = [210, 120, 130]
            result = self.game_end_format_image(cropped_image_array, red, "Defeat")
            if type(result) is not bool:
                reference_dictionary = {
                    'Defeat': self.gameEndReference["Defeat"]
                }
                potential = self.what_image_is_this(np.asarray(result), reference_dictionary)
                print('Defeat Potential: ' + str(potential["Defeat"]))
                if potential["Defeat"] > self.imageThreshold["Defeat"]:  # max 7200
                    self.objectiveProgress["gameEnd"] = "Defeat"
                    print("Defeat! :(")
                    self.set_game_over()
        if (mode == "for_reference") and (type(result) is not bool):
            # save image
            result.save("Debug\\Game End.png", "PNG")

    def game_end_format_image(self, image_array, color, mode):
        """ Identifies if the game is over by checking for "Victory" or "Defeat"

        :param image_array: Numpy Array of screen shot
        :param color: List of RGB pixels to be used as middle for thresholding
        :param mode: String, used for specifying debugging or saving for reference
        :return: None
        """

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

        # get dimensions to cut top edge
        for index, this_row in enumerate(rows_to_cut):
            if index != 0:
                if previous_row + 1 != this_row:
                    new_dimensions["start_y"] = previous_row
                    break
            previous_row = this_row
        # get dimensions to cut bottom edge
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
        img = Image.fromarray(cropped_image_array)
        img.save("Debug\\" + mode + ".png", "PNG")

        new_cropped_image_array = self.cut_image(cropped_image_array, new_dimensions)
        img = Image.fromarray(new_cropped_image_array)
        scaled_image_array = self.threshold(np.asarray((img.resize((160, 45), Image.BILINEAR))))
        scaled_image = Image.fromarray(scaled_image_array)

        # save image
        scaled_image.save("Debug\\" + mode + " scaled.png", "PNG")

        if len(scaled_image_array[0]) != len(self.gameEndReference["Victory"][0])\
                and len(scaled_image_array) != len(self.gameEndReference["Victory"]):
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
            "1.24": {
                "assault": {
                    "quick": {
                        "point1": {
                            "start_x": 916,
                            "end_x": 928,
                            "start_y": 132,
                            "end_y": 146
                        },
                        "point2": {
                            "start_x": 991,
                            "end_x": 1003,
                            "start_y": 132,
                            "end_y": 146
                        }
                    },
                    "competitive": {
                        "point1": {
                            "start_x": 916,
                            "end_x": 928,
                            "start_y": 134,
                            "end_y": 148
                        },
                        "point2": {
                            "start_x": 991,
                            "end_x": 1003,
                            "start_y": 134,
                            "end_y": 148
                        }
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
                    },
                    "competitive": {
                        "offense_score": {
                            'start_x': 802,
                            'end_x': 818,
                            'start_y': 88,
                            'end_y': 111
                        },
                        "defense_score": {
                            'start_x': 1096,
                            'end_x': 1112,
                            'start_y': 88,
                            'end_y': 111
                        }
                    }
                },
                "escort": {
                    "quick": {
                        "lock": {
                            "start_x": 953,
                            "end_x": 965,
                            "start_y": 130,
                            "end_y": 144
                        },
                        "progress_bar": {
                            "start_x": 787,
                            "end_x": 1135,
                            "start_y": 137,
                            "end_y": 148
                        }
                    },
                    'competitive': {
                        'lock': {
                            "start_x": 953,
                            "end_x": 965,
                            "start_y": 132,
                            "end_y": 146
                        },
                        "progress_bar": {
                            "start_x": 787,
                            "end_x": 1135,
                            "start_y": 138,
                            "end_y": 150
                        }
                    }
                },
                "transition": {
                    "quick": {
                        "point1": {
                            "start_x": 919,
                            "end_x": 931,
                            "start_y": 132,
                            "end_y": 146
                        },
                        "done": {
                            "start_x": 760,
                            "end_x": 772,
                            "start_y": 132,
                            "end_y": 146
                        },
                        "progress_bar": {
                            "start_x": 824,
                            "end_x": 1172,
                            "start_y": 137,
                            "end_y": 148
                        }
                    },
                    "competitive": {
                        "point1": {
                            "start_x": 919,
                            "end_x": 931,
                            "start_y": 133,
                            "end_y": 147
                        },
                        "done": {
                            "start_x": 761,
                            "end_x": 773,
                            "start_y": 133,
                            "end_y": 147
                        },
                        "progress_bar": {
                            "start_x": 824,
                            "end_x": 1172,
                            "start_y": 132,
                            "end_y": 142
                        }
                    }
                },
                'competitive': {
                    'offense': {
                        'start_x': 760,
                        'end_x': 880,
                        'y': 100
                    },
                    'defense': {
                        'start_x': 1030,
                        'end_x': 1180,
                        'y': 100
                    }
                },
                'game_end': {
                    'quick': {
                        'start_x': 630,
                        'end_x': 1316,
                        'start_y': 440,
                        'end_y': 633
                    },
                    'competitive': {
                        'start_x': 730,
                        'end_x': 1200,
                        'start_y': 270,
                        'end_y': 410
                    }
                },
                'map': {
                    'Hero Select': {
                        'normal': {
                            'start_x': 67,
                            'end_x': 492,  # 271,
                            'start_y': 198,
                            'end_y': 248
                        },
                        'lijiang': {
                            'start_x': 294,
                            'end_x': 420,
                            'start_y': 201,
                            'end_y': 244
                        },
                        'game_type': {
                            'start_x': 60,
                            'end_x': 135,
                            'start_y': 168,
                            'end_y': 239
                        },
                        'extended': {
                            'start_x': 144,
                            'end_x': 706,  # 565,  # 344,
                            'start_y': 198,
                            'end_y': 248
                        }
                    },
                    'Tab': {
                        'normal': {
                            'start_x': 65,
                            'end_x': 285,
                            'start_y': 38,
                            'end_y': 51
                        }
                    }
                }
            }
        }
        return dimensions[self.game_version]
