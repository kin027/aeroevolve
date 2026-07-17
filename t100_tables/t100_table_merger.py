import pandas as pd
import glob
import os

# Get absolute path of the folder where this script lives
script_dir = os.path.dirname(os.path.abspath(__file__))

# Find files in that same folder
file_pattern = os.path.join(script_dir, "*.csv")
file_list = glob.glob(file_pattern)

# Fill t100_list
t100_list = [pd.read_csv(file) for file in file_list]

# Concatenate each df in db1c_list
t100_df = pd.concat(t100_list)

# Set the output path for the final parquet
output_path = os.path.join(script_dir, "..", "final_t100.parquet")

# Output final_t100.parquet
t100_df.to_parquet(output_path, index=False, compression = "snappy")
