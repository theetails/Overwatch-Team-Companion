from datetime import datetime


class Statistics:
    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.snapshots = []

    def add_snapshot(self, heroes, current_map, map_side, objective_progress, game_time):
        self.snapshots.append(SnapShot(heroes, current_map, map_side, objective_progress, game_time))

    def submit_stats(self, game_end, current_time):
        if self.snapshots is not None:
            path = "Debug"
            debug_file = open(path + "\\Statistics " + current_time + ".txt", 'w')
            for snapshot in self.snapshots:
                snapshot_values = snapshot.output_array()
                for snapshot_value in snapshot_values:
                    line_to_write = str(snapshot_value) + '\n'
                    debug_file.write(line_to_write)
                debug_file.write('\n')
            debug_file.write(game_end)


class SnapShot:
    def __init__(self, heroes, current_map, map_side, objective_progress, game_time):
        self.heroes = heroes
        self.current_map = current_map
        self.map_side = map_side
        self.objective_progress = objective_progress
        self.game_time = datetime.strftime(game_time, "%M:%S")

    def output_array(self):
        array = [self.game_time, self.heroes, self.current_map, self.map_side, self.objective_progress]
        return array


