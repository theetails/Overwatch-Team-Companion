from datetime import datetime, timedelta


class Statistics:
    def __init__(self, debug_mode):
        self.debug_mode = debug_mode
        self.snapshots = []
        self.round_start_time = []
        self.new_round = False
        self.previous_time = None
        self.temporary_round_start = False

    def add_snapshot(self, heroes, current_map, map_side, objective_progress, game_time, current_system_time):
        self.snapshots.append(
            SnapShot(heroes, current_map, map_side, objective_progress, game_time, current_system_time)
        )

        # calculate system_time -> best estimate
        current_game_time = self.calculate_current_time()
        # correct snapshots / delete snapshots between rounds
        self.correct_snapshots(current_game_time)

    def calculate_current_time(self):
        latest_snapshot = self.snapshots[-1]
        print("Round Start Time Array Length: " + str(len(self.round_start_time)))

        safe_to_adjust = False
        if "controlProgress" in latest_snapshot.objective_progress:
            if latest_snapshot.objective_progress["controlProgress"][0] not in [None, "Prepare"]:
                safe_to_adjust = True

        if latest_snapshot.game_time["verified"] and safe_to_adjust:
            current_game_time = latest_snapshot.game_time["datetime"]
            self.previous_time = current_game_time
            print("Verified Game Time: " + datetime.strftime(current_game_time, "%M:%S"))
            game_time_delta = timedelta(minutes=current_game_time.minute, seconds=current_game_time.second)
            calculated_round_start_time = latest_snapshot.system_time - game_time_delta

            if len(self.round_start_time) > 0:
                system_start_time_difference = abs(
                    (self.round_start_time[-1]["start_time"] - calculated_round_start_time).total_seconds())
                print("Start Time Difference: " + str(system_start_time_difference))
                if system_start_time_difference > 1:
                    if self.temporary_round_start:
                        self.round_start_time[-1]["start_time"] = calculated_round_start_time
                        self.temporary_round_start = False
                    else:
                        previous_verified_snapshot = None
                        for snapshot in reversed(self.snapshots[:-1]):
                            if snapshot.game_time["verified"]:
                                previous_verified_snapshot = snapshot
                                break
                        if previous_verified_snapshot is None:
                            self.round_start_time = []
                            self.round_start_time.append({
                                "start_time": calculated_round_start_time,
                                "game_time": current_game_time
                            })
                        else:
                            previous_verified_game_time = previous_verified_snapshot.game_time["datetime"]
                            game_time_difference = abs(
                                (latest_snapshot.game_time["datetime"] - previous_verified_game_time).total_seconds())
                            print("Game Time Difference: " + str(game_time_difference))
                            if game_time_difference < 1.5:
                                previous_round_game_time_difference = (
                                    latest_snapshot.game_time["datetime"] - self.round_start_time[-1][
                                        "game_time"]).total_seconds()
                                # if previous_round_game_time_difference < 1:
                                    # del self.round_start_time[-1]
                                previous_verified_snapshot.game_time["verified"] = False
                            else:
                                self.round_start_time.append({
                                    "start_time": calculated_round_start_time,
                                    "game_time": current_game_time
                                })
            else:
                self.round_start_time.append({
                    "start_time": calculated_round_start_time,
                    "game_time": current_game_time
                })
        elif not safe_to_adjust:
            if self.previous_time is not None and not latest_snapshot.game_time["verified"]:
                if self.snapshots[-2].objective_progress["controlProgress"][0] not in [None, "Prepare"]:
                    current_game_time = self.previous_time
                    game_time_delta = timedelta(minutes=self.previous_time.minute, seconds=self.previous_time.second)
                    calculated_round_start_time = latest_snapshot.system_time - game_time_delta
                    self.round_start_time.append({
                        "start_time": calculated_round_start_time,
                        "game_time": self.previous_time
                    })
                    self.temporary_round_start = True
                else:
                    current_game_time = self.previous_time
            elif latest_snapshot.game_time["verified"]:
                self.previous_time = latest_snapshot.game_time["datetime"]
                current_game_time = self.previous_time
                game_time_delta = timedelta(minutes=current_game_time.minute, seconds=current_game_time.second)
                calculated_round_start_time = latest_snapshot.system_time - game_time_delta
                self.round_start_time[-1] = {
                    "start_time": calculated_round_start_time,
                    "game_time": current_game_time
                }
                self.temporary_round_start = True
            elif self.previous_time is not None:
                current_game_time = self.previous_time
            else:
                current_game_time = datetime.min
            # TODO keep looping previous game time
        else:
            if len(self.round_start_time) == 0:
                current_game_time = datetime.min
                self.previous_time = current_game_time
            else:
                system_time_difference = latest_snapshot.system_time - self.round_start_time[-1]["start_time"]
                current_game_time = datetime.min + system_time_difference
                self.previous_time = current_game_time

        print("Current Game Time: " + datetime.strftime(current_game_time, "%M:%S"))
        return current_game_time

    def correct_snapshots(self, current_game_time):
        count = 0
        for snapshot in reversed(self.snapshots):
            if snapshot.game_time["verified"]:
                break
            elif snapshot.game_time["datetime"]:
                count = count + 1

    def submit_stats(self, game_end, current_time):
        if self.snapshots is not None:
            path = "Debug"
            current_time_string = datetime.strftime(current_time, "%m-%d-%y %H-%M-%S")
            debug_file = open(path + "\\Statistics " + current_time_string + ".txt", 'w')
            for snapshot in self.snapshots:
                snapshot_values = snapshot.output_all()
                for snapshot_value in snapshot_values:
                    line_to_write = str(snapshot_value) + '\n'
                    debug_file.write(line_to_write)
                debug_file.write('\n')
            debug_file.write(game_end + '\n')
            debug_file.write(current_time_string + '\n')


class SnapShot:
    def __init__(self, heroes, current_map, map_side, objective_progress, game_time, system_time):
        self.heroes = heroes
        self.current_map = current_map
        self.map_side = map_side
        self.objective_progress = objective_progress
        self.game_time = game_time  # ["datetime", "verified"]
        self.system_time = system_time

    def output_all(self):
        game_time_string = datetime.strftime(self.game_time["datetime"], "%M:%S")
        system_time_string = datetime.strftime(self.system_time, "%m-%d-%y %H-%M-%S")
        array = [
            game_time_string,
            system_time_string,
            self.heroes,
            self.current_map,
            self.map_side,
            self.objective_progress
        ]
        return array
