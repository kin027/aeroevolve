from network_analyzer import NetworkAnalyzer

T100_PATH = "final_t100.parquet"
AIRPORTS_PATH = "airports.csv"


def main():
    # Create NetworkAnalyzer object
    analyzer = NetworkAnalyzer(T100_PATH, AIRPORTS_PATH)

    # Call run method for analyzer
    analyzer.run()


main()
