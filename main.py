from suspended_flight_routes_analyzer import SuspendedFlightRoutesAnalyzer

T100_FOLDER_PATH = "raw_T100_tables"

def main():
    # Create SuspendedFlightRoutesAnalyzer object
    analyzer = SuspendedFlightRoutesAnalyzer(T100_FOLDER_PATH)

    # Call run method for analyzer
    analyzer.run()

main()