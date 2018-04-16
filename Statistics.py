from datetime import datetime, timedelta
import json
import requests
# import copy


class Statistics:
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.snapshots = []
        self.round_start_time = []
        self.new_round = False
        self.previous_time = None
        self.temporary_round_start = False

        '''
        objectiveProgress = {
            "currentType": None,
            "gameEnd": False,
            "gameOver": False,
            "unlocked": False
            
            # Assault & Transition
            "assaultPoint": False
            "assaultPointProgress": None
            
            # Escort & Transition
            "escortProgress": []
            
            # Control
            "controlProgress": [this_status, our_progress, their_progress, this_side]
        }            
        '''

    def add_snapshot(self, heroes, current_map, map_side, objective_progress, game_time, current_system_time):
        self.snapshots.append(
            SnapShot(heroes, current_map, map_side, objective_progress, game_time, current_system_time)
        )

        # calculate system_time -> best estimate
        self.calculate_current_time()

    def calculate_current_time(self):
        current_game_time = datetime.min
        latest_snapshot = self.snapshots[-1]
        # print("Round Start Time Array Length: " + str(len(self.round_start_time)))

        safe_to_adjust = False
        # Control
        if "controlProgress" in latest_snapshot.objective_progress:
            if latest_snapshot.objective_progress["controlProgress"][0] not in [None, "Prepare"]:
                safe_to_adjust = True
        elif latest_snapshot.objective_progress["unlocked"]:
            # Assault, Escort, Transition
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
                                # TODO Remove?
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
                # Control
                if "controlProgress" in self.snapshots[-2].objective_progress:
                    if self.snapshots[-2].objective_progress["controlProgress"][0] not in [None, "Prepare"]:
                        current_game_time = self.previous_time
                        game_time_delta = timedelta(
                            minutes=self.previous_time.minute,
                            seconds=self.previous_time.second)
                        calculated_round_start_time = latest_snapshot.system_time - game_time_delta
                        self.round_start_time.append({
                            "start_time": calculated_round_start_time,
                            "game_time": self.previous_time
                        })
                        self.temporary_round_start = True
                    else:
                        current_game_time = self.previous_time
                elif self.snapshots[-2].objective_progress["unlocked"]:
                    # Assault, Escort, Transition
                    current_game_time = self.previous_time
                    game_time_delta = timedelta(
                        minutes=self.previous_time.minute,
                        seconds=self.previous_time.second)
                    calculated_round_start_time = latest_snapshot.system_time - game_time_delta
                    self.round_start_time.append({
                        "start_time": calculated_round_start_time,
                        "game_time": self.previous_time
                    })
                    self.temporary_round_start = True
            elif latest_snapshot.game_time["verified"]:
                self.previous_time = latest_snapshot.game_time["datetime"]
                current_game_time = self.previous_time
                game_time_delta = timedelta(minutes=current_game_time.minute, seconds=current_game_time.second)
                calculated_round_start_time = latest_snapshot.system_time - game_time_delta
                if len(self.round_start_time) == 0:
                    self.round_start_time.append({
                        "start_time": calculated_round_start_time,
                        "game_time": current_game_time
                    })
                else:
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

    def correct_snapshots(self):
        # TODO account for time prior to first recorded round_start_time
        print("correct snapshots")
        print(self.round_start_time)
        if self.round_start_time[0]["game_time"].minute > 0 or self.round_start_time[0]["game_time"].second > 0:
            zero_system_time = self.round_start_time[0]["start_time"] \
                               - timedelta(minutes=self.round_start_time[0]["game_time"].minute,
                                           seconds=self.round_start_time[0]["game_time"].second)
            self.round_start_time[0] = {
                "game_time": datetime.min,
                "start_time": zero_system_time
            }

        round_start_time_length = len(self.round_start_time)
        round_start_time_index = 1
        snapshots = list(reversed(self.snapshots))
        new_snapshots = []
        print("Snapshot Length: " + str(len(snapshots)))
        for number, snapshot in enumerate(snapshots):
            # Fix Times

            # print(number)
            # print("Game Time: " + datetime.strftime(snapshot.game_time["datetime"], "%M:%S"))
            # print("System Time: " + datetime.strftime(snapshot.system_time, "%m-%d-%y %H-%M-%S"))
            loop_completed = False
            while not loop_completed:
                if round_start_time_index > round_start_time_length:
                    print("Step 1: prevent index beyond length")
                    loop_completed = True
                    continue
                current_round_times = self.round_start_time[-round_start_time_index]
                if current_round_times["start_time"] < snapshot.system_time:
                    print("Step 2: Time Correctly Synced")
                    system_time_delta = snapshot.system_time - current_round_times["start_time"]
                    game_time_delta = system_time_delta - timedelta(
                        minutes=current_round_times["game_time"].minute,
                        seconds=current_round_times["game_time"].second)
                    game_time = current_round_times["game_time"] + game_time_delta

                    # Fix Blank Heroes
                    for team_number, team in enumerate(snapshot.heroes):
                        for hero_number, hero in enumerate(team):
                            if hero == "blank" and len(new_snapshots) > 0:
                                print("blank hero")
                                snapshots[number].heroes[team_number][hero_number] = new_snapshots[-1].heroes[team_number][hero_number]
                    new_snapshots.append((snapshots[number]))
                    new_snapshots[-1].game_time["datetime"] = game_time
                    loop_completed = True
                    print(system_time_delta)
                    print(game_time)
                    continue
                if round_start_time_index + 1 > round_start_time_length:
                    print("Step 3: prevent index of next round_start_time beyond length")
                    loop_completed = True
                    continue
                previous_round_times = self.round_start_time[-(round_start_time_index + 1)]
                previous_round_end_time = previous_round_times["start_time"] + timedelta(
                    minutes=previous_round_times["game_time"].minute,
                    seconds=previous_round_times["game_time"].second)
                if snapshot.system_time > previous_round_end_time:
                    print("Step 4: before round started")
                    loop_completed = True
                else:
                    round_start_time_index = round_start_time_index + 1
                    print("Step 5: next round_start_time")
        self.snapshots = list(reversed(new_snapshots))

        # for number, snapshot in enumerate(new_snapshots):
            # print(number)
            # print("Game Time: " + datetime.strftime(snapshot.game_time["datetime"], "%M:%S"))
            # print("System Time: " + datetime.strftime(snapshot.system_time, "%m-%d-%y %H-%M-%S"))

    def condense_snapshots(self):
        print("condense snapshots")
        # snapshots = list(reversed(self.snapshots))
        new_snapshots = []

        for number, snapshot in enumerate(self.snapshots):
            if number == 0:

                continue
            # sta


            # print(number)
            # print("Game Time: " + datetime.strftime(snapshot.game_time["datetime"], "%M:%S"))
            # print("System Time: " + datetime.strftime(snapshot.system_time, "%m-%d-%y %H-%M-%S"))
            loop_completed = False
            while not loop_completed:
                if round_start_time_index > round_start_time_length:
                    print("Step 1: prevent index beyond length")
                    loop_completed = True
                    continue
                current_round_times = self.round_start_time[-round_start_time_index]
                if current_round_times["start_time"] < snapshot.system_time:
                    print("Step 2: Time Correctly Synced")
                    system_time_delta = snapshot.system_time - current_round_times["start_time"]
                    game_time_delta = system_time_delta - timedelta(
                        minutes=current_round_times["game_time"].minute,
                        seconds=current_round_times["game_time"].second)
                    game_time = current_round_times["game_time"] + game_time_delta
                    new_snapshots.append((snapshots[number]))
                    new_snapshots[-1].game_time["datetime"] = game_time
                    loop_completed = True
                    print(system_time_delta)
                    print(game_time)
                    continue
                if round_start_time_index + 1 > round_start_time_length:
                    print("Step 3: prevent index of next round_start_time beyond length")
                    loop_completed = True
                    continue
                previous_round_times = self.round_start_time[-(round_start_time_index + 1)]
                previous_round_end_time = previous_round_times["start_time"] + timedelta(
                    minutes=previous_round_times["game_time"].minute,
                    seconds=previous_round_times["game_time"].second)
                if snapshot.system_time > previous_round_end_time:
                    print("Step 4: before round started")
                    loop_completed = True
                else:
                    round_start_time_index = round_start_time_index + 1
                    print("Step 5: next round_start_time")
        self.snapshots = list(reversed(new_snapshots))

        # for number, snapshot in enumerate(new_snapshots):
        # print(number)
        # print("Game Time: " + datetime.strftime(snapshot.game_time["datetime"], "%M:%S"))
        # print("System Time: " + datetime.strftime(snapshot.system_time, "%m-%d-%y %H-%M-%S"))

    def submit_stats(self, game_end, current_time):
        """
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
        """
        # correct snapshot times and objective progress, delete those from between rounds
        self.save_shapshots_for_debugging()
        self.correct_snapshots()
        # self.condense_snapshots()

        snapshot_list = []

        if self.snapshots is not None:
            path = "Debug"
            current_time_string = datetime.strftime(current_time, "%m-%d-%y %H-%M-%S")
            debug_file = open(path + "\\Statistics Corrected " + current_time_string + ".txt", 'w')
            for snapshot in self.snapshots:
                snapshot_values = snapshot.output_all()
                snapshot_list.append(snapshot_values)
                for snapshot_value in snapshot_values:
                    line_to_write = str(snapshot_value) + '\n'
                    debug_file.write(line_to_write)
                debug_file.write('\n')
            snapshot_list.append({
                "Game End": game_end,
                "Game End Time": current_time_string
            })
            debug_file.write(game_end + '\n')
            debug_file.write(current_time_string + '\n')

            # json_string = json.dumps(snapshot_list)
            # requests.post("http://voxter.mooo.com:1080/snapshot", data=json_string)

    def save_shapshots_for_debugging(self):
        snapshot_output_list = []
        for snapshot in self.snapshots:
            snapshot_output_list.append(snapshot.output_all())
        with open("Debug\\Snapshot.txt", 'w') as file:
            json.dump(snapshot_output_list, file)

    def load_snapshot(self, file_name):
        with open("Debug\\" + file_name, 'r') as file_data:
            json_data = json.loads(file_data.read())
            for saved_snapshot in json_data:
                self.add_snapshot(saved_snapshot[2], saved_snapshot[3], saved_snapshot[4], saved_snapshot[5],
                                  {"datetime": datetime.strptime(saved_snapshot[0], "%M:%S"), "verified": True},
                                  datetime.strptime(saved_snapshot[1], "%m-%d-%y %H-%M-%S"))

    @staticmethod
    def send_saved_snapshot():
        with open("Debug\\Snapshot.txt", 'r') as file_data:
            json_data = json.loads(file_data.read())
            print(json_data)
            response = requests.post("http://overwatch.app/snapshot", json=json_data)
            print(response.text)


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


if __name__ == "__main__":
    this = Statistics()
    this.load_snapshot("Snapshot-1.txt")
    this.submit_stats("Victory", datetime.now())
    # this.send_saved_snapshot()
