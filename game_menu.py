from tkinter import *
from snake_game import SnakeGame
from libemg.gui import GUI
from libemg.data_handler import OnlineDataHandler, OfflineDataHandler, RegexFilter
from libemg.streamers import myo_streamer
from libemg.feature_extractor import FeatureExtractor
from libemg.emg_predictor import OnlineEMGClassifier, EMGClassifier

class Menu:
    def __init__(self):
        # Myo Streamer - start streaming the myo data 
        streamer, sm = myo_streamer()
        self.sm = sm
        self.streamer = streamer
        self.classifier = None

        # UI related initialization
        self.window = None
        self.initialize_ui()

    def initialize_ui(self):
        # Create the simple menu UI:
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.title("Game Menu")
        self.window.geometry("500x200")

        # Label 
        Label(self.window, font=("Arial bold", 20), text = 'LibEMG - Snake Demo').pack(pady=(10,20))
        # Train Model Button
        Button(self.window, font=("Arial", 18), text = 'Train Model', command=self.launch_training).pack(pady=(0,20))
        # Play Snake Button
        Button(self.window, font=("Arial", 18), text = 'Play Snake', command=self.play_snake).pack()

        self.window.mainloop()

    def play_snake(self):
        self.window.destroy()
        self.set_up_classifier()
        SnakeGame().run_game()
        # Its important to stop the classifier after the game has ended
        # Otherwise it will continuously run in a seperate process
        self.classifier.stop_running()
        self.initialize_ui()

    def launch_training(self):
        self.window.destroy()
        # Launch training ui
        training_ui = GUI(OnlineDataHandler(self.sm), width=700, height=700, gesture_height=300, gesture_width=300)
        training_ui.download_gestures([1,2,3,4,5], "images/")
        training_ui.start_gui()
        self.initialize_ui()

    def set_up_classifier(self):
        WINDOW_SIZE = 40 
        WINDOW_INCREMENT = 20

        # Step 1: Parse offline training data
        dataset_folder = 'data/'
        regex_filters = [
            RegexFilter(left_bound = "C_", right_bound="_R", values = ["0","1","2","3","4"], description='classes'),
            RegexFilter(left_bound = "R_", right_bound="_emg.csv", values = ["0", "1", "2"], description='reps'),
        ]

        offline_dh = OfflineDataHandler()
        offline_dh.get_data(folder_location=dataset_folder, regex_filters=regex_filters, delimiter=",")
        train_windows, train_metadata = offline_dh.parse_windows(WINDOW_SIZE, WINDOW_INCREMENT)

        # Step 2: Extract features from offline data
        fe = FeatureExtractor()
        feature_list = fe.get_feature_groups()['HTD']
        training_features = fe.extract_features(feature_list, train_windows)

        # Step 3: Dataset creation
        data_set = {}
        data_set['training_features'] = training_features
        data_set['training_labels'] = train_metadata['classes']

        # Step 4: Create the EMG Classifier
        o_classifier = EMGClassifier(model="LDA")
        o_classifier.fit(feature_dictionary=data_set)

        # Step 5: Create online EMG classifier and start classifying.
        self.classifier = OnlineEMGClassifier(o_classifier, WINDOW_SIZE, WINDOW_INCREMENT, OnlineDataHandler(self.sm), feature_list)
        self.classifier.run(block=False) # block set to false so it will run in a seperate process.

    def on_closing(self):
        # Clean up all the processes that have been started
        self.window.destroy()
        self.streamer.cleanup()
        
if __name__ == "__main__":
    menu = Menu()