import tkinter
import re
import sys


class AppUI(tkinter.Tk):
    def __init__(self, this_app_controller, loop, interval=0.01):
        super().__init__()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.width = 300
        self.height = 250
        self.currentGroupID = None
        self.geometry('{}x{}'.format(self.width, self.height))
        self.loop = loop
        self.tasks = []
        self.groupIDDisplayWindow = None
        self.thisAppController = this_app_controller
        self.updater(interval)

        self.mainMenuWindow = None
        self.errorMessageLabel = None
        self.groupIDLabel = None

    async def start_ui(self):
        self.resizable(width=False, height=False)
        self.title("Main Menu")
        self.mainMenuWindow = tkinter.Frame(self, width=self.width, height=self.height)
        self.mainMenuWindow.pack(fill="both", expand=True, padx=20, pady=20)
        tkinter.Button(self.mainMenuWindow, text="Start Game Watcher", command=self.get_group_id).pack(fill="x")
        tkinter.Button(self.mainMenuWindow, text="Developer Tools", command=self.open_developer_tools).pack(fill="x")

    def open_developer_tools(self):
        self.mainMenuWindow.destroy()
        self.title("Developer Tools")
        developer_tools_window = tkinter.Frame(self, width=self.width, height=self.height)
        developer_tools_window.pack(fill="both", expand=True, padx=20, pady=20)
        tkinter.Button(developer_tools_window, text="Hero Reference: Create Images",
                       command=self.create_hero_images).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Hero Reference: Create TXT",
                       command=self.create_hero_reference).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Map Reference -Hero Select: Create Image",
                       command=self.create_map_image_hero_select).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Map Reference -Tab: Create Image",
                       command=self.create_map_image_tab).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Map Reference -Objectives: Create Image",
                       command=self.create_map_image_objective).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Map Reference: Create TXT",
                       command=self.create_map_reference).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Digit Reference: Create Images",
                       command=self.create_digit_images).pack(fill="x")
        tkinter.Button(developer_tools_window, text="Digit Reference: Create TXT",
                       command=self.create_digit_references).pack(fill="x")

    def get_group_id(self):
        self.mainMenuWindow.destroy()
        self.title("Group ID Input")
        error_window = tkinter.Frame(self)
        error_window.pack(side="bottom", fill=tkinter.X, expand=True, padx=20)
        group_id_entry_window = tkinter.Frame(self, width=self.width, height=self.height)
        group_id_entry_window.pack(side="bottom", fill=tkinter.X, expand=True, padx=20)
        group_id_entry_label = tkinter.Label(group_id_entry_window, text="Group ID")
        group_id_entry_label.pack(side="left")
        group_id_entry = tkinter.Entry(group_id_entry_window, width=20)
        group_id_entry.pack(side="left")
        submit_group_id = tkinter.Button(group_id_entry_window, text="Submit",
                                         command=lambda: self.check_group_id(group_id_entry))
        submit_group_id.pack(side="left")
        self.errorMessageLabel = tkinter.Label(error_window, text="", fg="red")
        self.errorMessageLabel.pack()

    def check_group_id(self, entry):
        entry_text = entry.get()
        entry_text = entry_text.lower().strip()
        if entry_text == self.currentGroupID:
            self.errorMessageLabel["text"] = "You are already in this room"
        elif len(entry_text) < 5:
            self.errorMessageLabel["text"] = "ID is too short"
        elif len(entry_text) > 5:
            self.errorMessageLabel["text"] = "ID is too long"
        elif re.search('[a-z0-9]{5}', entry_text):
            for task in self.tasks:
                task.cancel()
                self.thisAppController.unsubscribe_from_current()
            self.tasks = []
            self.wm_state('iconic')
            self.currentGroupID = entry_text
            self.errorMessageLabel["text"] = ""
            self.in_room_ui(entry_text)
            self.tasks.append(self.loop.create_task(self.thisAppController.subscribe_to_id(entry_text)))

        else:
            self.errorMessageLabel["text"] = "Only Alphanumeric Characters"

    def in_room_ui(self, entry_text):
        if self.groupIDDisplayWindow is None:
            self.groupIDDisplayWindow = tkinter.Frame(self)
            self.groupIDDisplayWindow.pack(side="top", fill=tkinter.X, expand=True, padx=20)
            group_id_display_label = tkinter.Label(self.groupIDDisplayWindow, text="Current Room: ")
            group_id_display_label.pack(side="left")
            self.groupIDLabel = tkinter.Label(self.groupIDDisplayWindow, text=entry_text)
            self.groupIDLabel.pack(side="left")
        else:
            self.groupIDLabel['text'] = entry_text

    def create_hero_images(self):
        self.thisAppController.create_images_for_hero_reference()

    def create_hero_reference(self):
        self.thisAppController.create_hero_references()

    def create_map_image_hero_select(self):
        self.thisAppController.create_images_for_map_reference_hero_select()

    def create_map_image_tab(self):
        self.thisAppController.create_images_for_map_reference_tab()

    def create_map_image_objective(self):
        self.thisAppController.create_images_for_map_reference_objective()

    def create_map_reference(self):
        self.thisAppController.create_map_references()

    def create_digit_images(self):
        self.thisAppController.create_digit_images()

    def create_digit_references(self):
        self.thisAppController.create_digit_references()

    def updater(self, interval):
        self.update()
        self.loop.call_later(interval, self.updater, interval)

    def close(self):
        self.loop.stop()
        sys.exit()
