import pandas as pd
import tkinter
from tkinter import simpledialog, messagebox
from pathlib import Path
import plotly.express as px
import calendar

TITLE = "Suspended Flight Routes"


class SuspendedFlightRoutesAnalyzer:
    def __init__(self, t100_folder_path, airports_csv_path):
        # Set file path attributes
        self.folder_path = t100_folder_path
        self.airports_csv_path = airports_csv_path

        # Create new Tkinter window then withdraw it
        self.window = tkinter.Tk()
        self.window.withdraw()

        # Attributes to be filled out in later methods
        self.origin_airport = None
        self.origin_airport_lat = None
        self.origin_airport_lon = None
        self.most_recent_T100_df = pd.DataFrame()
        self.all_past_T100_df = pd.DataFrame()
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

        # Last item (index -1) in list is most recent T-100 CSV, read it
        self.most_recent_T100_df = pd.read_csv(folder_path / files[-1])

        # Remove last item from the list
        files.pop()

        # Read each remaining T-100 CSV and store each into an array
        temp_dfs = [pd.read_csv(folder_path / file) for file in files]

        # Concatenate the list into self.all_past_T100_df
        self.all_past_T100_df = pd.concat(temp_dfs, ignore_index=True)

        # Read airports.csv
        self.airports_df = pd.read_csv(self.airports_csv_path)

    # Method to get and validate airport code from user
    def get_origin_airport(self):
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
            valid_origin_airports = set(self.all_past_T100_df["ORIGIN"].unique())

            # Validate user-entered origin airport
            if origin_airport in valid_origin_airports:  # Valid airport
                # Set origin_airport attribute to result
                self.origin_airport = origin_airport

                # Get origin airport coordinates from airports_df
                self.origin_airport_lat = self.airports_df.loc[
                    self.airports_df["iata_code"] == self.origin_airport, "latitude_deg"
                ].values[0]
                self.origin_airport_lon = self.airports_df.loc[
                    self.airports_df["iata_code"] == self.origin_airport,
                    "longitude_deg",
                ].values[0]

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
        # Clean both T-100 table dfs
        df_list = [self.most_recent_T100_df, self.all_past_T100_df]

        for n in range(0, 2):
            # Drop NA values
            df_list[n] = df_list[n].dropna()

            # Filter T-100 so that DEPARTURES_PERFORMED > 4 (at least once a week frequency on average, exclude diversions, etc.)
            df_list[n] = df_list[n][df_list[n]["DEPARTURES_PERFORMED"] > 4]

            # Filter T-100 so that PASSENGERS > 0 (exclude cargo)
            df_list[n] = df_list[n][df_list[n]["PASSENGERS"] > 0]

            # Filter T-100 so that CLASS is "F" (Scheduled Passenger/ Cargo Service F) (exclude non-scheduled flights)
            df_list[n] = df_list[n][df_list[n]["CLASS"] == "F"]

            # Filter T-100 so that ORIGIN is self.origin_airport
            df_list[n] = df_list[n][df_list[n]["ORIGIN"] == self.origin_airport]

        # Reassign cleaned dfs to attributes
        self.most_recent_T100_df = df_list[0]
        self.all_past_T100_df = df_list[1]

        # Filter all_past_T100_df so that DEST values are not DEST values in most_recent_T100_df
        self.all_past_T100_df = self.all_past_T100_df[
            ~self.all_past_T100_df["DEST"].isin(self.most_recent_T100_df["DEST"])
        ]

        # Sort all_past_T100_df by recency in descending order
        self.all_past_T100_df = self.all_past_T100_df.sort_values(
            by=["YEAR", "MONTH"], ascending=[False, False]
        )

        # Keep only the top-most row for a given destination (the most recent month of operation)
        self.all_past_T100_df = self.all_past_T100_df.drop_duplicates(subset="DEST")

        # Merge iata_code field in airports_df with DEST field airport code in all_past_T100_df
        self.all_past_T100_df = self.all_past_T100_df.merge(
            right=self.airports_df[["iata_code", "latitude_deg", "longitude_deg"]],
            how="left",
            left_on="DEST",
            right_on="iata_code",
        )

        # Convert MONTH field to month name
        self.all_past_T100_df["MONTH"] = self.all_past_T100_df["MONTH"].map(
            lambda x: calendar.month_name[x]
        )

        print(
            self.all_past_T100_df[
                ["UNIQUE_CARRIER", "DEST", "DEST_CITY_NAME", "MONTH", "YEAR"]
            ].head(30)
        )

    # Method to create the map
    def create_map(self):
        # Create the map with suspended airports
        hover_cols = {
            "latitude_deg": False,
            "longitude_deg": False,
            "DEST": False,
            "DEST_CITY_NAME": True,
            "DEST_COUNTRY_NAME": True,
            "MONTH": True,
            "YEAR": True,
            "UNIQUE_CARRIER_NAME": True,
        }

        custom_labels = {
            "DEST_CITY_NAME": "City",
            "DEST_COUNTRY_NAME": "Country",
            "MONTH": "Month Suspended",
            "YEAR": "Year Suspended",
            "UNIQUE_CARRIER_NAME": "Airline last served",
        }

        final_map = px.scatter_map(
            data_frame=self.all_past_T100_df,
            lat="latitude_deg",
            lon="longitude_deg",
            text="DEST",
            hover_data=hover_cols,
            labels=custom_labels,
            zoom=2,
            center={"lat": self.origin_airport_lat, "lon": self.origin_airport_lon},
        )

        # Add origin point
        final_map.add_trace(
            dict(
                type="scattermap",
                lat=[self.origin_airport_lat],
                lon=[self.origin_airport_lon],
                text=[self.origin_airport],
                mode="markers+text",
                textposition="top center",
                textfont=dict(
                    color="#000000", family="Helvetica", size=18, weight="bold"
                ),
                marker=dict(size=18, color="#000000"),
                showlegend=False,
            )
        )

        # Add title and subtitle, change map base
        final_map.update_layout(
            title={
                "text": f"Suspended flight routes from {self.origin_airport} since 1990",
                "subtitle": {
                    "text": "Based on Bureau of Transportation Statistics (BTS) T-100 tables. For more details about a specific airport, hover on its mark on the map."
                },
            },
            mapbox_style="basic",
            showlegend=False,
        )

        final_map.show()

    # Method to run all previous methods
    def run(self):
        # Call get_origin_airport method
        if not self.get_origin_airport():
            self.window.destroy()
            return

        # Call analyze_suspended_routes method
        self.analyze_suspended_routes()

        # Call create_map method
        self.create_map()
