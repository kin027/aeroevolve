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
            title=TITLE,
            prompt="Enter a three-character IATA airport code:\n\n(If a non-U.S. airport code is entered, \nonly routes to the U.S. will be shown.)",
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

    def analyze_routes(self):
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
            # Filter self_T100_df by user-selected airline
            self.T100_df = self.T100_df[
                self.T100_df["UNIQUE_CARRIER_NAME"] == self.airline
            ]

        # Build map layout
        self.app.layout = self.build_layout()
        self.register_callbacks()

    # Method to construct and return layout tree
    def build_layout(self):
        return html.Div(
            # Overall style
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "98vh",
                "margin": "0",
                "padding": "10px",
                "fontFamily": "Helvetica",
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
                        tooltip={"placement": "bottom", "always_visible": False},
                        updatemode="drag",
                        allow_direct_input=False,  # Hide input box
                        included=False,
                    ),
                    style={
                        "flex": "1",
                        "paddingTop": "20px",
                    },
                ),
                # Div for bottom data source note
                html.Div(
                    "Based on Bureau of Transportation Statistics (BTS) T-100 Segment (All Carriers) tables.",
                    style={
                        "fontSize": "18px",
                        "color": "#A7A9AC",
                        "marginLeft": "10px",
                        "marginBottom": "10px",
                        "padding": "0px",
                    },
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
        # Constants for map
        TYPEFACE = "Helvetica"
        HOVER_FONT_SIZE = 12
        SMALL_FONT_SIZE = 12
        MEDIUM_FONT_SIZE = 18
        LARGE_FONT_SIZE = 36
        ORIGIN_COLOR = "#000000"
        DEST_COLOR = "#00933c"
        ORIGIN_LAT = self.airports_df.loc[
            self.airports_df["iata_code"] == self.origin_airport, "latitude_deg"
        ].values[0]
        ORIGIN_LON = self.airports_df.loc[
            self.airports_df["iata_code"] == self.origin_airport, "longitude_deg"
        ].values[0]

        # Get year and month from timeline position
        target_year, target_month, target_month_name = self.timeline[slider_position]

        # Filter self.T00_df by year and month, put into new df
        dest_df = self.T100_df[
            (self.T100_df["YEAR"] == target_year)
            & (self.T100_df["MONTH"] == target_month)
        ].copy()

        # Copy dest_df to create origin_df
        origin_df = dest_df.copy()

        # Change the coordinates to match that of the origin airport
        origin_df["LAT"] = ORIGIN_LAT
        origin_df["LON"] = ORIGIN_LON

        # Apply even index to origin_df
        origin_df.index = range(0, len(origin_df) * 2, 2)

        # Apply odd index to dest_df
        dest_df.index = range(1, len(dest_df) * 2, 2)

        # Concat origin_df and dest_df
        routes_df = pd.concat([origin_df, dest_df])

        # Create a new column "ALL_CARRIERS" to deal with duplication of lines due to multiple airlines operating the same route
        dest_df = (
            dest_df.groupby(
                [
                    "ROUTE",
                    "LAT",
                    "LON",
                    "DEST",
                    "DEST_CITY_NAME",
                ]
            )["UNIQUE_CARRIER_NAME"]
            .apply(lambda x: ", ".join(sorted(x.unique())))
            .reset_index(name="ALL_CARRIERS")
        )

        # Base map
        display_map = px.line_geo(
            title=f"Departures from {self.origin_airport} for {self.airline} in {target_month_name} {target_year}",
            projection="natural earth",
        )

        # If there are routes to display
        if not routes_df.empty:
            # Trace for routes
            routes_map = px.line_geo(
                data_frame=routes_df,
                lat="LAT",
                lon="LON",
                line_group="ROUTE",
            )
            routes_map.update_traces(
                line=dict(color=DEST_COLOR),
                hoverinfo="none",
            )
            for route in routes_map.data:
                display_map.add_trace(route)

            # Trace for destination airports
            display_map.add_trace(
                go.Scattergeo(
                    lat=dest_df["LAT"],
                    lon=dest_df["LON"],
                    mode="text",
                    text=dest_df["DEST"],
                    textposition="top center",
                    textfont=dict(
                        family=TYPEFACE,
                        size=SMALL_FONT_SIZE,
                        color=DEST_COLOR,
                    ),
                    showlegend=False,
                    customdata=dest_df[
                        ["DEST", "DEST_CITY_NAME", "ALL_CARRIERS"]
                    ].values,
                    hovertemplate=(
                        "Destination Airport: %{customdata[0]}<br>"
                        "Destination City: %{customdata[1]}<br>"
                        "Airline(s): %{customdata[2]}<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor=DEST_COLOR,
                        font_family=TYPEFACE,
                        font_color="#FFFFFF",
                        font_size=HOVER_FONT_SIZE,
                    ),
                )
            )

        # Trace for origin airport
        display_map.add_trace(
            go.Scattergeo(
                lat=[ORIGIN_LAT],
                lon=[ORIGIN_LON],
                mode="markers+text",
                text=[self.origin_airport],
                textposition="top center",
                textfont=dict(
                    family=TYPEFACE,
                    size=MEDIUM_FONT_SIZE,
                    color=ORIGIN_COLOR,
                ),
                marker=dict(
                    size=SMALL_FONT_SIZE,
                    color=ORIGIN_COLOR,
                ),
                showlegend=False,
                customdata=origin_df["ORIGIN_CITY_NAME"],
                hovertemplate="%{customdata}<extra></extra>",
                hoverlabel=dict(
                    bgcolor=ORIGIN_COLOR,
                    font_family=TYPEFACE,
                    font_color="#FFFFFF",
                    font_size=HOVER_FONT_SIZE,
                ),
            )
        )

        # General map layout
        display_map.update_layout(
            title_font_family=TYPEFACE,
            title_font_size=LARGE_FONT_SIZE,
            title_font_color=ORIGIN_COLOR,
            hovermode="closest",
            hoverdistance=30,
            transition_duration=200,
            height=None,
        )

        return display_map

    # Method to run all previous methods
    def run(self):
        # Call get_user_selections method
        if self.get_user_selections():
            # Call analyze_routes method
            self.analyze_routes()

            # Destroy Tkinter window
            # self.window.destroy()

            # Open Dash server
            server_thread = threading.Thread(
                target=self.app.run,
                kwargs={"debug": False, "port": 8050, "use_reloader": False},
                daemon=True,
            )

            server_thread.start()

            # Show window for map
            webview.create_window(
                title=TITLE, url="http://127.0.0.1:8050/", maximized=True
            )
            webview.start()

        # Destroy Tkinter window
        self.window.destroy()
