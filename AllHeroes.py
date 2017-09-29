import numpy as np
from PIL import Image

from GameObject import GameObject
from Hero import Hero


class AllHeroes(GameObject):
    correctHeroThreshold = 2850
    heroesDictionary = {}
    heroesList = []

    def __init__(self, game_version, debug_mode):
        self.game_version = game_version
        self.debugMode = debug_mode
        self.characterReferences = self.read_references("Reference\\HeroImageList.txt")
        self.characterBlurReferences = self.read_references("Reference\\HeroImageBlurList.txt")
        for x in range(1, 13):
            self.heroesDictionary[x] = Hero(x)

    def main(self, screen_image_array, current_time, current_view):
        hero_range = []
        if current_view == "Hero Select":
            hero_range = range(1, 7)
        elif current_view == "Tab":
            hero_range = range(1, 13)

        failed_heroes = []
        for hero_number in hero_range:
            this_hero = self.heroesDictionary[hero_number]
            result = self.identify_hero(screen_image_array, this_hero, current_view)
            if not result:
                failed_heroes.append(hero_number)
                print(str(hero_number) + " Failed")
            else:
                print(this_hero.currentHero)

        if len(failed_heroes) > 0:
            if self.debugMode:
                for hero_number in failed_heroes:
                    self.heroesDictionary[hero_number].save_debug_data(current_time)
                screen_shot = Image.fromarray(screen_image_array)
                screen_shot.save("Debug\\Potential " + current_time + " fullscreen" + ".png", "PNG")
            for hero_number in failed_heroes:
                self.heroesDictionary[hero_number].revert_previous_hero()

        # check for entire enemy team -> unknowns
        if current_view == "Tab":
            all_unknown = True
            for hero_number, enemy_hero in self.heroesDictionary.items():
                if hero_number in range(7, 13):
                    if enemy_hero.currentHero != "unknown":
                        all_unknown = False
            if all_unknown:
                for hero_number, enemy_hero in self.heroesDictionary.items():
                    if hero_number in range(7, 13):
                        enemy_hero.revert_previous_hero()
        return current_view

    def heroes_to_list(self):
        current_heroes_list = [[], []]

        for heroNumber, hero in self.heroesDictionary.items():
            if heroNumber > 6:
                this_row = 1
            else:
                this_row = 0
            current_heroes_list[this_row].append(hero.get_hero_number())
        if current_heroes_list != self.heroesList:
            self.heroesList = current_heroes_list
            return True
        else:
            return False

    def identify_hero(self, screen_img_array, this_hero, view):
        if view == "Tab":
            hero_coordinates = this_hero.screenPositionTab
        else:
            hero_coordinates = this_hero.screenPositionCharacterSelect

        this_hero_img = screen_img_array[
                        hero_coordinates["start_y"]: hero_coordinates["end_y"],
                        hero_coordinates["start_x"]: hero_coordinates["end_x"]
                        ]  # crop to Hero
        # Make Black & White based off average value
        this_hero_img_threshold = self.threshold(np.asarray(this_hero_img))
        this_hero.set_image_array(this_hero_img)  # save IMG to Hero

        this_hero_references = {}
        other_hero_references = {}

        # 1) check if it is the same hero as previously
        if this_hero.currentHero is not None:
            for character, reference in self.characterReferences.items():
                character_split = character.split("-")
                if character_split[0] == this_hero.currentHero:
                    this_hero_references[character] = reference
                else:
                    other_hero_references[character] = reference
            result = self.get_hero_from_potential(this_hero, this_hero_img_threshold, this_hero_references)
        else:
            other_hero_references = self.characterReferences
            result = False

        # 2) check for blurred versions if on hero select and slot number is 1
        if not result:
            if view == "Hero Select" and this_hero.slotNumber == 1:
                result = self.get_hero_from_potential(this_hero, this_hero_img_threshold, self.characterBlurReferences)
        # 3) check standard array of heroes
        if not result:
            result = self.get_hero_from_potential(this_hero, this_hero_img_threshold, other_hero_references)
        return result

    def get_hero_from_potential(self, this_hero, image, character_references):
        potential = self.what_image_is_this(image, character_references)  # compare to References
        this_hero.set_potential(potential)
        identified_hero = max(potential.keys(), key=(lambda k: potential[k]))
        if potential[identified_hero] > self.correctHeroThreshold:  # if enough pixels are the same
            this_hero_split = identified_hero.split("-")
            this_hero.set_hero(this_hero_split[0])
            if this_hero.slotNumber == 1 and (this_hero_split[0] == "searching" or this_hero_split[0] == "unknown"):
                # The player cannot be "searching" or "unknown", reduces errors
                return False
            else:
                return True
        else:
            return False

    def check_for_change(self):
        heroes_list_change = self.heroes_to_list()  # Save heroes to heroesDictionary
        return heroes_list_change

    def broadcast_heroes(self, broadcaster):
        publish_list = ["heroes", self.heroesList]
        if broadcaster != "debug":
            broadcaster.publish(broadcaster.subscriptionString, publish_list)

    def clear_enemy_heroes(self, broadcaster):
        for heroNumber, hero in self.heroesDictionary.items():
            if heroNumber in range(7, 13):
                hero.clear_hero()
        self.heroes_to_list()
        if broadcaster != "debug":
            self.broadcast_heroes(broadcaster)

    def change_heroes(self, incoming_heroes):
        incoming_heroes_dictionary = {}
        count = 1
        for row in incoming_heroes:
            for heroNumber in row:
                incoming_heroes_dictionary[count] = heroNumber
                count = count + 1
        for heroNumber, hero in self.heroesDictionary.items():
            this_hero_name = hero.get_hero_name_from_number(incoming_heroes_dictionary[heroNumber])
            hero.set_hero(this_hero_name)
        self.heroes_to_list()
