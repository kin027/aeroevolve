import pandas as pd
from tkinter import *
from tkinter import simpledialog, messagebox
from pathlib import Path
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import calendar
import webview
import threading

TITLE = "AeroEvolve"


class NetworkAnalyzer:
    def __init__(self, t100_folder_path, airports_csv_path):
        # File path attributes
        self.folder_path = t100_folder_path
        self.airports_csv_path = airports_csv_path

        # Tkinter window followed by withdrawal
        self.window = Tk()
        self.window.withdraw()

        # Attributes to be filled out in later methods
        self.airline = None
        self.origin_airport = None
        self.T100_df = pd.DataFrame()
        self.airports_df = pd.read_csv(self.airports_csv_path)

        # Airline filtering box
        self.airline_filter_selection_box = None
        self.airline_filter_selection = None

        # Interactive map
        self.app = Dash(__name__)
        self.timeline = []

    # Method to all T-100 CSVs and store dataframes in attributes
    def read_T100_csvs(self):
        # T-100 fields are DepPerformed, Passengers, UniqueCarrier, UniqueCarrierName, Origin, OriginCityName, OriginCountryName, Dest, DestCityName, DestCountryName, Year, Month, Class

        # Create temporary loading window
        loading_win = Toplevel(self.window)
        loading_win.title(TITLE)
        label = Label(
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

        # Use Path to get all CSVs in self.folder_path
        folder_path = Path(self.folder_path)

        # Store all csv file names in a list
        files = [file.name for file in folder_path.iterdir() if file.suffix == ".csv"]

        # Sort that list into alphabetical order
        files.sort()

        # Read each T-100 CSV and store each into an array
        temp_dfs = [pd.read_csv(folder_path / file) for file in files]

        # Concatenate the list into self.T100_df
        T100_df = pd.concat(temp_dfs, ignore_index=True)

        # Create mew MONTH_NAME field for month name
        T100_df["MONTH_NAME"] = T100_df["MONTH"].map(lambda x: calendar.month_name[x])

        # Set the final result to self.T100_Df
        self.T100_df = T100_df

        # Set self.timeline
        temp_df = self.T100_df.drop_duplicates(subset=["YEAR", "MONTH"])
        temp_df = temp_df.sort_values(by=["YEAR", "MONTH"], ascending=True)
        self.timeline = [
            (row.YEAR, row.MONTH, row.MONTH_NAME) for row in temp_df.itertuples()
        ]

    # Method for button clicked when user selects an airline
    def button_clicked(self):
        # Read the selected airline and store it in self.airline
        self.airline = self.airline_filter_selection.get()

        # Release event grab
        self.airline_filter_selection_box.grab_release()

        # Destroy the box
        self.airline_filter_selection_box.destroy()
        self.window.update()

    # Method to get and validate airport code from user
    def get_user_selections(self):
        # Ask user for airport code
        origin_airport = simpledialog.askstring(
            title=TITLE, prompt="Enter a three-character IATA airport code:"
        )

        if origin_airport:
            # Convert user input to uppercase
            origin_airport = origin_airport.upper()

            # Call self.read_T100_csvs()
            self.read_T100_csvs()

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
        ).drop(columns="iata_code")

        # Rename coordinate columns
        self.T100_df = self.T100_df.rename(
            columns={"latitude_deg": "LAT", "longitude_deg": "LON"}
        )

        # Create new column for ROUTE (e.g. DFW-HND)
        self.T100_df["ROUTE"] = self.T100_df["ORIGIN"] + "-" + self.T100_df["DEST"]

        # Ask user for specific airline to filter it down to
        airlines = (
            self.T100_df["UNIQUE_CARRIER_NAME"]
            .sort_values(ascending=True)
            .unique()
            .tolist()
        )

        airlines.insert(0, "All Airlines")

        # Create window
        self.airline_filter_selection_box = Toplevel(padx=20, pady=20)
        self.airline_filter_selection_box.title(TITLE)
        self.airline_filter_selection = StringVar(value="All Airlines")

        # Create label
        label = Label(
            master=self.airline_filter_selection_box,
            text=f"Select an airline to see its network from {self.origin_airport},\nor All Airlines to see the entire network from {self.origin_airport}:",
        )
        label.grid(column=0, row=0)

        # Create menu dropdown
        OptionMenu(
            self.airline_filter_selection_box, self.airline_filter_selection, *airlines
        ).grid(column=0, row=1)

        # Create menu button
        button = Button(
            master=self.airline_filter_selection_box,
            text="OK",
            command=self.button_clicked,
        )
        button.grid(column=0, row=2)

        # Show the box
        self.airline_filter_selection_box.grab_set()
        self.window.wait_window(self.airline_filter_selection_box)
        self.window.update()

        # If self.airline is not All Airlines:
        if self.airline != "All Airlines":
            # Filter self_T100_df by self.airline
            self.T100_df = self.T100_df[
                self.T100_df["UNIQUE_CARRIER_NAME"] == self.airline
            ]

        # Build map layout
        self.app.layout = self.build_layout()
        self.register_callbacks()

    # Method to construct and return layout tree (for self.app_layout)
    def build_layout(self):
        return html.Div(
            # Overall style
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "98vh",
                "margin": "0",
                "padding": "10px",
                "font-family": "helvetica",
                "font-size": 12,
                "color": "#000",
            },
            children=[
                # Div for map
                html.Div(
                    dcc.Graph(
                        id="map",
                        style={
                            "height": "100%",
                            "width": "100%",
                        },
                    ),
                    style={"flex": "9"},
                ),
                # Div for slider
                html.Div(
                    dcc.Slider(
                        min=0,
                        max=len(self.timeline) - 1,
                        step=1,
                        value=0,
                        marks={
                            i: (str(time[0]) if time[1] == 1 else "")
                            for i, time in enumerate(self.timeline)
                        },
                        id="slider",
                        tooltip={},
                        updatemode="drag",
                    ),
                    style={"flex": "1", "paddingTop": "20px"},
                ),
            ],
        )

    # Method to update map whenever the slider is moved
    def register_callbacks(self):
        @self.app.callback(
            Output("map", "figure"),
            Input("slider", "value"),
        )
        def update(slider_val):
            return self.update_map(slider_val)

    def update_map(self, slider_position):
        # Get year and month from timeline position
        target_year, target_month, target_month_name = self.timeline[slider_position]

        # Filter self.T00_df more into a new df
        dest_df = self.T100_df[
            (self.T100_df["YEAR"] == target_year)
            & (self.T100_df["MONTH"] == target_month)
        ].copy()

        # Copy dest_df to create origin_df
        origin_df = dest_df.copy()

        # Change the coordinates to match that of the origin airport
        origin_df["LAT"] = self.airports_df.loc[
            self.airports_df["iata_code"] == self.origin_airport, "latitude_deg"
        ].values[0]

        origin_df["LON"] = self.airports_df.loc[
            self.airports_df["iata_code"] == self.origin_airport, "longitude_deg"
        ].values[0]

        # Apply even index to origin_df
        origin_df.index = range(0, len(origin_df) * 2, 2)

        # Apply odd index to dest_df
        dest_df.index = range(1, len(dest_df) * 2, 2)

        # Concat origin_df and dest_df
        display_df = pd.concat([origin_df, dest_df])

        if not display_df.empty:
            # Create map
            display_map = px.line_geo(
                data_frame=display_df,
                lat="LAT",
                lon="LON",
                hover_data=["ORIGIN_CITY_NAME", "DEST_CITY_NAME"],
                line_group="ROUTE",
                center={
                    "lat": 0,
                    "lon": 0,
                },
                title=f"Departures from {self.origin_airport} for {self.airline} in {target_month_name} {target_year}",
                projection="natural earth",
            )

            # Layout options
            display_map.update_traces(
                line=dict(color="#00933c"),
            )

            display_map.update_layout(
                map_style="light",
                transition_duration=200,
                height=None,
                geo=dict(
                    countrycolor="#444",
                    countrywidth=1,
                    oceancolor="#3399FF",
                    showframe=False,
                    showland=True,
                ),
            )

            return display_map
        else:
            empty_map = go.Figure()

            empty_map.update_layout(
                map_style="open-street-map",
                title=f"There weren't any departures from {self.origin_airport} for {self.airline} in {target_month_name} {target_year}",
            )

            return empty_map

    # Method to run all previous methods
    def run(self):
        # Call get_origin_airport method
        if self.get_user_selections():
            # Call analyze_suspended_routes method
            self.analyze_suspended_routes()

            # Destroy Tkinter window
            self.window.destroy()

            # Open Dash erver
            server_thread = threading.Thread(
                target=self.app.run,
                kwargs={"debug": False, "port": 8050, "use_reloader": False},
                daemon=True,
            )

            server_thread.start()

            # Show the map
            webview.create_window(
                title=TITLE, url="http://127.0.0.1:8050/", maximized=True
            )
            webview.start()
        else:
            # Destroy Tkinter window
            self.window.destroy()
