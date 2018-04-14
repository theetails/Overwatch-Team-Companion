class MapState:
    map = [None]
    map_side = "offense"

    image_array = None
    view_potential = None
    map_potential = None

    game_mode = None

    def get_current_map(self):
        return self.map[0]
