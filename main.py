from suspended_flight_routes_analyzer import SuspendedFlightRoutesAnalyzer

T100_FOLDER_PATH = "raw_T100_tables"
AIRPORTS_CSV_PATH = "airports.csv"


def main():
    # Create SuspendedFlightRoutesAnalyzer object
    analyzer = SuspendedFlightRoutesAnalyzer(T100_FOLDER_PATH, AIRPORTS_CSV_PATH)

    # Call run method for analyzer
    analyzer.run()


main()
