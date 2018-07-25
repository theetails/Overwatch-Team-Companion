import operator
from PIL import Image


class Hero:
    heroesReferenceDictionary = {
        "unknown": "blank", "searching": "blank", "dva": 1, "reinhardt": 2, "roadhog": 3, "winston": 4, "zarya": 5,
        "tracer": 6, "mccree": 7, "pharah": 8, "reaper": 9, "soldier76": 10, "genji": 11, "bastion": 12, "hanzo": 13,
        "junkrat": 14, "mei": 15, "torbjorn": 16, "widowmaker": 17, "lucio": 18, "mercy": 19, "symmetra": 20,
        "zenyatta": 21, "ana": 22, "sombra": 23, "orisa": 24, "doomfist": 25, "moira": 26, "brigitte": 27}

    def __init__(self, this_slot_number):
        self.currentHero = None
        self.previousHero = None

        self.screenPositionTab = None
        self.screenPositionCharacterSelect = None

        self.currentImageArray = None
        self.potential = None
        self.previousImageArray = None
        self.previousPotential = None

        self.slotNumber = this_slot_number
        self.calculate_screen_position()

        self.hero_changed = False

    def calculate_screen_position(self):
        """ Calculates this hero's positions in a view when identifying

        :return: None
        """

        character_select_start_y = 604
        character_select_end_y = 646

        if self.slotNumber <= 6:
            start_y = 585  # 595
            end_y = 627  # 637
            x_hero_number = self.slotNumber
        else:
            start_y = 300  # 290
            end_y = 342  # 332
            x_hero_number = self.slotNumber - 6

        start_x = 249 + (x_hero_number * 192)
        end_x = 326 + (x_hero_number * 192)

        self.screenPositionCharacterSelect = {
            "start_x": start_x,
            "end_x": end_x,
            "start_y": character_select_start_y,
            "end_y": character_select_end_y
        }
        self.screenPositionTab = {
            "start_x": start_x,
            "end_x": end_x,
            "start_y": start_y,
            "end_y": end_y
        }

    def save_debug_data(self, current_time):
        # save image
        img = Image.fromarray(self.currentImageArray)
        img.save("Debug\\Potential " + current_time + " " + str(self.slotNumber) + ".png", "PNG")
        # save potential
        debug_file = open('Debug\\Potential ' + current_time + " " + str(self.slotNumber) + '.txt', 'w')
        for potentialCharacter, value in sorted(self.potential.items(), key=operator.itemgetter(1), reverse=True):
            line_to_write = str(value) + ': ' + potentialCharacter + '\n'
            debug_file.write(line_to_write)

    def set_potential(self, this_potential):
        self.previousPotential = self.potential
        self.potential = this_potential

    def set_image_array(self, image_array):
        self.previousImageArray = self.currentImageArray
        self.currentImageArray = image_array

    def set_hero(self, hero):
        self.previousHero = self.currentHero
        self.currentHero = hero
        self.hero_changed = True

    def revert_previous_hero(self):
        if self.previousHero is not None and self.hero_changed:
            self.currentHero = self.previousHero
            self.previousHero = None
            self.potential = self.previousPotential
            self.previousPotential = None
            self.currentImageArray = self.previousImageArray
            self.previousImageArray = None

    def get_hero_number(self):
        if self.currentHero is None:
            return "blank"
        else:
            return self.heroesReferenceDictionary[self.currentHero]

    def get_hero_name_from_number(self, hero_number):
        if hero_number == "blank":
            return None
        for referenceName, referenceNumber in self.heroesReferenceDictionary.items():
            if hero_number == referenceNumber:
                return referenceName

    def clear_hero(self):
        self.currentHero = None
        self.currentImageArray = None
        self.potential = None

        self.previousHero = None
        self.previousImageArray = None
        self.previousPotential = None
