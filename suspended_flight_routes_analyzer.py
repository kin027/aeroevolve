import pandas as pd
import tkinter
from tkinter import simpledialog, messagebox
from pathlib import Path # Handles files

TITLE = "Suspended Flight Routes"

class SuspendedFlightRoutesAnalyzer:
    def __init__(self, folder_path):
        # Set self.folder_path to folder path passed as argument at class instantiation
        self.folder_path = folder_path

        # Create new Tkinter window then withdraw it
        self.window = tkinter.Tk()
        self.window.withdraw()

        # Attributes to be filled out in later methods
        self.origin_airport = None
        self.most_recent_T100_df = pd.DataFrame()
        self.all_past_T100_df = pd.DataFrame()

    # Method to read all CSVs and store dataframes in attributes
    def read_and_store_csvs(self):
        # Use Path to get all CSVs in self.folder_path
        folder_path = Path(self.folder_path)

        # Store all csv file names in a list
        files = [file.name for file in folder_path.iterdir() if file.suffix == ".csv"]

        # Sort that list into alphabetical order
        files.sort()

        # Last item (index -1) in list is most recent T-100 CSV, read it
        self.most_recent_T100_df = pd.read_csv(folder_path / files[-1])

        # Remove last item from the list
        files.pop()

        # Read each remaining T-100 CSV and store each into an array
        temp_dfs = [pd.read_csv(folder_path / file) for file in files]

        # Concatenate the list into self.all_past_T100_df
        self.all_past_T100_df = pd.concat(temp_dfs, ignore_index = True)

        print(f"Shape: {self.all_past_T100_df.shape}")

    # Method to get and validate airport code from user
    def get_origin_airport(self):
        # Ask user for airport code
        origin_airport = simpledialog.askstring(title = TITLE, prompt = "Enter a three-character IATA airport code\nfor an airport in the U.S.:")

        if origin_airport:
            # Convert user input to uppercase
            origin_airport = origin_airport.upper()

            # Create temporary loading window
            loading_win = tkinter.Toplevel(self.window)
            loading_win.title(TITLE)
            label = tkinter.Label(loading_win, text="Loading...", font = ("Helvetica", 24), padx = 50, pady = 50, anchor = "center")
            label.pack()
            loading_win.update()

            # Close the window
            loading_win.destroy()

            # Call read_and_store_csvs method
            self.read_and_store_csvs()

            print("CSVs read")

            # Get a set of valid origin airport codes
            valid_origin_airports = set(self.all_past_T100_df["ORIGIN"].unique())

            # Validate user-entered origin airport
            if origin_airport in valid_origin_airports: # Valid airport
                # Set origin_airport attribute to result
                self.origin_airport = origin_airport

                return True
            else: # Invalid airport
                # Display message box for error message
                messagebox.showerror(message = "Airport is nonexistent, does not have scheduled commercial air service, or "
                                               "never had service to the U.S. since 1990", title = TITLE)
                return False
        else:
            return False

    def analyze_suspended_routes(self):
        # Clean both T-100 table dfs
        df_list = [self.most_recent_T100_df, self.all_past_T100_df]

        for n in range(0, 2):
            # Drop NA values
            df_list[n].dropna(inplace = True)

            # Filter T-100 so that DEPARTURES_SCHEDULED > 0 (exclude diversions, etc.)
            df_list[n] = df_list[n][df_list[n]["DEPARTURES_SCHEDULED"] >= 10]

            # Filter T-100 so that CLASS is "F" (Scheduled Passenger/ Cargo Service F) (exclude non-scheduled flights)
            df_list[n] = df_list[n][df_list[n]["CLASS"] == "F"]

            # Filter T-100 so that PASSENGERS > 0 (exclude cargo)
            df_list[n] = df_list[n][df_list[n]["PASSENGERS"] > 0]

            # Filter T-100 so that ORIGIN is self.origin_airport
            df_list[n] = df_list[n][df_list[n]["ORIGIN"] == self.origin_airport]

            #

        # Reassign cleaned dfs to attributes
        self.most_recent_T100_df = df_list[0]
        self.all_past_T100_df = df_list[1]

        # Filter all_past_T100_df so that DEST values are not DEST values in most_recent_T100_df
        self.all_past_T100_df = self.all_past_T100_df[~self.all_past_T100_df["DEST"].isin(self.most_recent_T100_df["DEST"])]

        self.all_past_T100_df.sort_values("YEAR", ascending = False, inplace = True)

        print(self.all_past_T100_df[["UNIQUE_CARRIER", "DEST", "DEST_CITY_NAME"]].drop_duplicates().head(30))


    # Method to run all previous methods
    def run(self):
        # Call get_origin_airport
        if not self.get_origin_airport():
            self.window.destroy()
            return

        # Call analyze_suspended_routes
        self.analyze_suspended_routes()