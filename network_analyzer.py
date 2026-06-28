import pandas as pd
import tkinter
from tkinter import simpledialog, messagebox
from pathlib import Path

import calendar

TITLE = "AeroEvolve"


class NetworkAnalyzer:
    def __init__(self, t100_folder_path, airports_csv_path):
        # Set file path attributes
        self.folder_path = t100_folder_path
        self.airports_csv_path = airports_csv_path

        # Create new Tkinter window then withdraw it
        self.window = tkinter.Tk()
        self.window.withdraw()

        # Attributes to be filled out in later methods
        self.airline_filter_selection_box = None
        self.airline_filter_selection = None
        self.airline = None
        self.origin_airport = None
        self.T100_df = pd.DataFrame()
        self.airports_df = pd.DataFrame()

    # Method to read all CSVs and store dataframes in attributes
    def read_and_store_csvs(self):
        # T-100 fields are DepPerformed, Passengers, UniqueCarrier, UniqueCarrierName, Origin, OriginCityName, OriginCountryName, Dest, DestCityName, DestCountryName, Year, Month, Class

        # Use Path to get all CSVs in self.folder_path
        folder_path = Path(self.folder_path)

        # Store all csv file names in a list
        files = [file.name for file in folder_path.iterdir() if file.suffix == ".csv"]

        # Sort that list into alphabetical order
        files.sort()

        # Read each remaining T-100 CSV and store each into an array
        temp_dfs = [pd.read_csv(folder_path / file) for file in files]

        # Concatenate the list into self.T100_df
        self.T100_df = pd.concat(temp_dfs, ignore_index=True)

        # Read airports.csv
        self.airports_df = pd.read_csv(self.airports_csv_path)

    # Method for button clicked when user selects an airline
    def button_clicked(self):
        # Read the selected airline and store it in self.airline
        self.airline = self.airline_filter_selection.get()

        # Destroy the box
        self.airline_filter_selection_box.destroy()

    # Method to get and validate airport code from user
    def get_user_selections(self):
        # Ask user for airport code
        origin_airport = simpledialog.askstring(
            title=TITLE, prompt="Enter a three-character IATA airport code:"
        )

        if origin_airport:
            # Convert user input to uppercase
            origin_airport = origin_airport.upper()

            # Create temporary loading window
            loading_win = tkinter.Toplevel(self.window)
            loading_win.title(TITLE)
            label = tkinter.Label(
                loading_win,
                text="Loading...",
                font=("Helvetica", 24),
                padx=50,
                pady=50,
                anchor="center",
            )
            label.pack()
            loading_win.update()

            # Close the window
            loading_win.destroy()

            # Call read_and_store_csvs method
            self.read_and_store_csvs()

            # Get a set of valid origin airport codes
            valid_origin_airports = set(self.T100_df["ORIGIN"].unique())

            # Validate user-entered origin airport
            if origin_airport in valid_origin_airports:  # Valid airport
                # Set origin_airport attribute to result
                self.origin_airport = origin_airport

                return True
            else:  # Invalid airport
                # Display message box for error message
                messagebox.showerror(
                    message="Airport is nonexistent or never had scheduled commercial passenger "
                    "air service to the U.S. since 1990.",
                    title=TITLE,
                )
                return False
        else:
            return False

    def analyze_suspended_routes(self):
        # Clean self.T100_df

        # Drop NA values
        self.T100_df = self.T100_df.dropna()

        # Filter T-100 so that DEPARTURES_PERFORMED > 4 (at least once a week frequency on average, exclude diversions, etc.)
        self.T100_df = self.T100_df[self.T100_df["DEPARTURES_PERFORMED"] > 4]

        # Filter T-100 so that PASSENGERS > 0 (exclude cargo)
        self.T100_df = self.T100_df[self.T100_df["PASSENGERS"] > 0]

        # Filter T-100 so that CLASS is "F" (Scheduled Passenger/ Cargo Service F) (exclude non-scheduled flights)
        self.T100_df = self.T100_df[self.T100_df["CLASS"] == "F"]

        # Filter T-100 so that ORIGIN is self.origin_airport
        self.T100_df = self.T100_df[self.T100_df["ORIGIN"] == self.origin_airport]

        # Drop duplicates by UNIQUE_CARRIER, DEST, MONTH, and YEAR
        self.T100_df = self.T100_df.drop_duplicates(
            subset=["UNIQUE_CARRIER", "DEST", "MONTH", "YEAR"]
        )

        # Sort all_past_T100_df by recency in descending order
        self.T100_df = self.T100_df.sort_values(
            by=["YEAR", "MONTH"], ascending=[False, False]
        )

        # Merge iata_code field in airports_df with DEST field airport code in all_past_T100_df for destination airport codes
        self.T100_df = self.T100_df.merge(
            right=self.airports_df[["iata_code", "latitude_deg", "longitude_deg"]],
            how="left",
            left_on="DEST",
            right_on="iata_code",
        )

        # Create new ORIGIN_LAT field
        self.T100_df["ORIGIN_LAT"] = self.airports_df.loc[
            self.airports_df["iata_code"] == self.origin_airport, "latitude_deg"
        ].values[0]

        # Create new ORIGIN_LON field
        self.T100_df["ORIGIN_LON"] = self.airports_df.loc[
            self.airports_df["iata_code"] == self.origin_airport, "longitude_deg"
        ].values[0]

        # Create mew MONTH_NAME field for month name
        self.T100_df["MONTH_NAME"] = self.T100_df["MONTH"].map(
            lambda x: calendar.month_name[x]
        )

        # Ask user for specific airline to filter it down to
        airlines = (
            self.T100_df["UNIQUE_CARRIER_NAME"]
            .sort_values(ascending=True)
            .unique()
            .tolist()
        )

        airlines.insert(0, "[All]")

        # Create window
        self.airline_filter_selection_box = tkinter.Toplevel(padx=20, pady=20)
        self.airline_filter_selection_box.title(TITLE)
        self.airline_filter_selection = tkinter.StringVar(value="[All]")

        # Create label
        label = tkinter.Label(
            master=self.airline_filter_selection_box,
            text=f"Select an airline to see its network from {self.origin_airport},\nor [All] to see its entire network from there:",
        )
        label.grid(column=0, row=0)

        # Create menu dropdown
        tkinter.OptionMenu(
            self.airline_filter_selection_box, self.airline_filter_selection, *airlines
        ).grid(column=0, row=1)

        # Create menu dropdown
        button = tkinter.Button(
            master=self.airline_filter_selection_box,
            text="OK",
            command=self.button_clicked,
        )
        button.grid(column=0, row=2)

        # Show the box
        self.airline_filter_selection_box.grab_set()
        self.airline_filter_selection_box.wait_window()

        # If self.airline is not "[All]":
        if self.airline != "[All]":
            # Filter self_T100_df one by self.airline
            self.T100_df = self.T100_df[
                self.T100_df["UNIQUE_CARRIER_NAME"] == self.airline
            ]

        print(
            self.T100_df[
                [
                    "UNIQUE_CARRIER",
                    "DEST",
                    "DEST_CITY_NAME",
                    "MONTH",
                    "YEAR",
                ]
            ].head(30)
        )

    # Method to create the map or update it whenever the slider is moved

    # Filter self.T00_df more

    # Create origin airport marker

    # Method to run all previous methods
    def run(self):
        # Call get_origin_airport method
        if self.get_user_selections():

            # Call analyze_suspended_routes method
            self.analyze_suspended_routes()

            # Call create_map method
            # self.create_map()

        self.window.destroy()
