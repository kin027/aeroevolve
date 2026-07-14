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
    def __init__(self, t100_folder_path, airports_path):
        # File path attributes
        self.folder_path = t100_folder_path

        # Tkinter window followed by withdrawal
        self.window = Tk()
        self.window.withdraw()

        # Attributes to be filled out in later methods
        self.airline = None
        self.origin_airport = None
        self.global_max_seats = None
        self.original_t100_df = None
        self.copy_t100_df = None
        self.airports_df = pd.read_csv(
            airports_path,
            usecols=["name", "iata_code", "latitude_deg", "longitude_deg"],
        )

        # Airline filtering box
        self.airline_filter_selection_box = None
        self.airline_filter_selection = None

        # Interactive map
        self.app = Dash(__name__)
        self.register_callbacks()
        self.timeline = []

    # Method to read all T-100 CSVs and perform basic data cleaning
    def read_csvs(self):
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

        # Concatenate each df into one large df
        t100_df = pd.concat(temp_dfs, ignore_index=True)

        # Perform basic data cleaning

        # Drop NA values
        t100_df = t100_df.dropna()

        # Filter T-100 so that DEPARTURES_PERFORMED > 4 (at least once a week frequency on average, exclude diversions, etc.)
        t100_df = t100_df[t100_df["DEPARTURES_PERFORMED"] > 4]

        # Filter T-100 so that SEATS > 0 (exclude cargo)
        t100_df = t100_df[t100_df["SEATS"] > 0]

        # Filter T-100 so that CLASS is "F" (Scheduled Passenger/ Cargo Service F) (exclude non-scheduled flights)
        t100_df = t100_df[t100_df["CLASS"] == "F"]

        # Create mew MONTH_NAME field for month name
        t100_df["MONTH_NAME"] = t100_df["MONTH"].map(lambda x: calendar.month_name[x])

        # Set self.timeline
        temp_df = t100_df.drop_duplicates(subset=["YEAR", "MONTH"])
        temp_df = temp_df.sort_values(by=["YEAR", "MONTH"], ascending=True)
        self.timeline = [
            (row.YEAR, row.MONTH, row.MONTH_NAME) for row in temp_df.itertuples()
        ]

        # Set the final result
        self.original_t100_df = t100_df

        # Create temporary copy and group by unique route and unique month
        global_max_seats_df = (
            t100_df.groupby(["YEAR", "MONTH", "ORIGIN", "DEST"])["SEATS"]
            .sum()
            .reset_index()
        )

        # Set self.global_max_seats to maximum value in SEATS field of global_max_seats_df
        self.global_max_seats = global_max_seats_df["SEATS"].max()

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
        result = None

        # Ask user for airport code
        origin_airport = simpledialog.askstring(
            title=TITLE,
            prompt="Enter a three-character IATA airport code:\n\n(If a non-U.S. airport code is entered, \nonly routes to the U.S. will be shown.)",
        )

        if origin_airport:
            # Convert user input to uppercase
            origin_airport = origin_airport.upper()

            # Get a set of valid origin airport codes
            valid_origin_airports = set(self.original_t100_df["ORIGIN"].unique())

            # Validate user-entered origin airport
            if origin_airport in valid_origin_airports:  # Valid airport
                # Set origin_airport attribute to result
                self.origin_airport = origin_airport

                result = "VALID"
            else:  # Invalid airport
                # Display message box for error message
                messagebox.showerror(
                    message="Airport is nonexistent or never had scheduled commercial passenger "
                    "air service to the U.S. since 1990.",
                    title=TITLE,
                )
                result = "INVALID"
        else:  # No response
            result = "EXIT"

        return result

    # Method to filter a copy of self.original_t100_df based on user selections
    def analyze_routes(self):
        # T-100 fields are DepPerformed, Seats, UniqueCarrierName, Origin, OriginCityName, Dest, DestCityName, Year, Month, Class

        # Create copy of original T-100 df
        self.copy_t100_df = self.original_t100_df.copy()

        # Filter T-100 so that ORIGIN is self.origin_airport
        self.copy_t100_df = self.copy_t100_df[
            self.copy_t100_df["ORIGIN"] == self.origin_airport
        ]

        # Ask user for specific airline to filter it down to
        airlines = (
            self.copy_t100_df["UNIQUE_CARRIER_NAME"]
            .sort_values(ascending=True)
            .unique()
            .tolist()
        )

        airlines.insert(0, "All Carriers")

        # Create window
        self.airline_filter_selection_box = Toplevel(padx=20, pady=20)
        self.airline_filter_selection_box.title(TITLE)
        self.airline_filter_selection = StringVar(value="All Carriers")

        # Create label
        label = Label(
            master=self.airline_filter_selection_box,
            text=f"Select an airline to see its network from {self.origin_airport},\nor All Carriers to see the entire network from {self.origin_airport}:",
        )
        label.grid(column=0, row=0)

        # Create menu dropdown
        OptionMenu(
            self.airline_filter_selection_box,
            self.airline_filter_selection,
            *airlines,
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

        # If user selected to filter by airline:
        if self.airline != "All Carriers":
            # Filter by self.airline
            self.copy_t100_df = self.copy_t100_df[
                self.copy_t100_df["UNIQUE_CARRIER_NAME"] == self.airline
            ]

        # Sort by recency in descending order
        self.copy_t100_df = self.copy_t100_df.sort_values(
            by=["YEAR", "MONTH"], ascending=[False, False]
        )

        # Get columns for airport coordinates
        self.copy_t100_df = self.copy_t100_df.merge(
            right=self.airports_df[["iata_code", "latitude_deg", "longitude_deg"]],
            how="left",
            left_on="DEST",
            right_on="iata_code",
        ).drop(columns="iata_code")

        # Rename coordinate columns
        self.copy_t100_df = self.copy_t100_df.rename(
            columns={"latitude_deg": "LAT", "longitude_deg": "LON"}
        )

        # Create new column for ROUTE (e.g. DFW-HND)
        self.copy_t100_df["ROUTE"] = (
            self.copy_t100_df["ORIGIN"] + "-" + self.copy_t100_df["DEST"]
        )

    # Method to construct and return layout tree
    def build_layout(self):
        return html.Div(
            # Overall style
            style={
                "display": "flex",
                "flexDirection": "column",
                "height": "98vh",
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
                    style={"flex": "3"},
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
                        "paddingLeft": "50px",
                        "paddingRight": "50px",
                        "marginTop": "50px",
                    },
                ),
                # Div for bottom data source note
                html.Div(
                    [
                        "Source: Bureau of Transportation Statistics (BTS).",
                        html.Br(),
                        "Line width reflects capacity (seats available) during a given month on a square root scale. If the origin airport is not in the U.S., only routes to the U.S. will be shown.",
                    ],
                    style={
                        "fontSize": "18px",
                        "color": "#A7A9AC",
                        "paddingBottom": "10px",
                        "paddingLeft": "10px",
                    },
                ),
            ],
        )

    # Method to update map whenever slider is moved
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
        MIN_LINE_WIDTH = 1
        MAX_LINE_WIDTH = 10

        # Get year and month from timeline position
        target_year, target_month, target_month_name = self.timeline[slider_position]

        # Create dest_df, which is source of info for all routes and is filtered by month and year
        dest_df = self.copy_t100_df[
            (self.copy_t100_df["YEAR"] == target_year)
            & (self.copy_t100_df["MONTH"] == target_month)
        ].copy()

        # Create base map
        display_map = px.line_geo(
            title=f"Departures from {self.origin_airport} for {self.airline} in {target_month_name} {target_year}",
            projection="natural earth",
        )

        if not dest_df.empty:
            # Copy dest_df to create origin_df
            origin_df = dest_df.copy()

            # Change the coordinates in origin_df to match that of the origin airport
            origin_df["LAT"] = ORIGIN_LAT
            origin_df["LON"] = ORIGIN_LON

            # Apply even index to origin_df
            origin_df.index = range(0, len(origin_df) * 2, 2)

            # Apply odd index to dest_df
            dest_df.index = range(1, len(dest_df) * 2, 2)

            # Create routes_df, which is exclusively used for plotting routes
            routes_df = pd.concat([origin_df, dest_df])

            # Create a new column "ALL_CARRIERS" to deal with duplication of lines due to multiple airlines operating the same route, and sum SEATS by route
            dest_df = (
                dest_df.groupby(
                    [
                        "ROUTE",
                        "LAT",
                        "LON",
                        "DEST",
                        "DEST_CITY_NAME",
                    ]
                )
                .agg(
                    ALL_CARRIERS=(
                        "UNIQUE_CARRIER_NAME",
                        lambda x: ", ".join(sorted(x.unique())),
                    ),
                    SEATS=("SEATS", "sum"),
                )
                .reset_index()
            )

            # Create trace for routes
            routes_map = px.line_geo(
                data_frame=routes_df,
                lat="LAT",
                lon="LON",
                line_group="ROUTE",
                color="ROUTE",
            )

            # From dest_df, create a dictionary of just ROUTE and SEATS to be used in for loop below
            seats_dict = dest_df.set_index("ROUTE")["SEATS"].to_dict()

            # Display line for each route
            for route in routes_map.data:
                # Use route to look up seats in seats_dict
                seats = seats_dict.get(route.name.replace("ROUTE=", ""), 0)

                # Calculate line width using square root scaling
                line_width = MIN_LINE_WIDTH + (
                    (seats ** (1 / 2)) / (self.global_max_seats ** (1 / 2))
                ) * (MAX_LINE_WIDTH - MIN_LINE_WIDTH)

                # Set route.line.width to line_width
                route.line = dict(color=DEST_COLOR, width=line_width)

                # Hide legend
                route.showlegend = False

                # Display line
                display_map.add_trace(route)

            # Create trace for destination airport labels and hover labels
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
                        ["DEST", "DEST_CITY_NAME", "ALL_CARRIERS", "SEATS"]
                    ].values,
                    hovertemplate=(
                        "Destination Airport: %{customdata[0]}<br>"
                        "Destination City: %{customdata[1]}<br>"
                        "Carrier(s): %{customdata[2]}<br>"
                        "Seats Available: %{customdata[3]}<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor=DEST_COLOR,
                        font_family=TYPEFACE,
                        font_color="#FFFFFF",
                        font_size=HOVER_FONT_SIZE,
                    ),
                )
            )
        else:  # No routes to display
            # Create origin_df just so hovering over origin airport in map shows a city name
            origin_df = pd.DataFrame(
                [{"ORIGIN_CITY_NAME": self.copy_t100_df.loc[0, "ORIGIN_CITY_NAME"]}]
            )

        # Create trace for origin airport
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

        # Change general map layout
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

    # Method to show the map
    def show_map(self):
        # Open Dash server
        server_thread = threading.Thread(
            target=self.app.run,
            kwargs={"debug": False, "port": 8050, "use_reloader": False},
            daemon=True,
        )

        server_thread.start()

        # Show window for map
        webview.create_window(title=TITLE, url="http://127.0.0.1:8050/", maximized=True)
        webview.start()

    # Method to run all previous methods
    def run(self):
        # Read CSVs
        self.read_csvs()

        user_selection_result = None

        # While the result of the function has something
        while user_selection_result != "EXIT":
            # Get user selections
            user_selection_result = self.get_user_selections()

            if user_selection_result == "VALID":
                # Analyze routes
                self.analyze_routes()

                # Build map layout
                self.app.layout = self.build_layout()

                # Show map
                self.show_map()

        # Destroy Tkinter window
        self.window.destroy()
