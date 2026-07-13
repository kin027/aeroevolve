from network_analyzer import NetworkAnalyzer

T100_FOLDER_PATH = "T100_tables"
AIRPORTS_CSV_PATH = "airports.csv"


def main():
    # Create NetworkAnalyzer object
    analyzer = NetworkAnalyzer(T100_FOLDER_PATH, AIRPORTS_CSV_PATH)

    # Call run method for analyzer
    analyzer.run()


main()
