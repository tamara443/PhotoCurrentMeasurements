import os
import re
import pandas as pd
import matplotlib.pyplot as plt


def extract_nm_number(filename):
    # Use regular expressions to extract the number in front of "nm"
    match = re.search(r'(\d+)nm', filename)
    if match:
        nm_number = int(match.group(1))
        return nm_number
    else:
        return None  # Return None if "nm" number is not found


def remove_outliers(df, n_std):
    mean = df.mean()
    sd = df.std()
    df = df[(df <= mean + (n_std * sd))]
    df = df[(df >= mean - (n_std * sd))]
    return df


# Specify the folder containing your data files
folder_path = ''

# List files and sort them based on the "nm" number
file_list = os.listdir(folder_path)
file_list = [filename for filename in file_list if filename.endswith(".dat") and extract_nm_number(filename) is not None]

# Extract and store numeric values along with the filenames
file_data = [(filename, extract_nm_number(filename)) for filename in file_list]

# Sort the list based on the extracted numeric values
file_data.sort(key=lambda x: x[1])

print(file_data)

# Create a list to collect the results for each file
results = []

# Loop through files in the sorted order
for filename, nm_number in file_data:
    if filename.endswith(".dat"):
        # Construct the full file path
        file_path = os.path.join(folder_path, filename)

        # Read the data from the file
        data = pd.read_csv(file_path, sep="\s+", usecols=[0, 1, 2], header=None)
        data = data.iloc[400:]
        data.columns = ["Time", "Current", "Voltage"]
        data["Time"] = data["Time"].astype(float)
        data["Current"] = data["Current"].astype(float)
        data["Voltage"] = data["Voltage"].astype(float)
        time_data = data["Time"]
        current_data = data["Current"]
        current_largest = current_data.nlargest(n=80)
        current_smallest = current_data.nsmallest(n=80)
        current_largest = remove_outliers(current_largest, 3)
        current_max = current_largest.mean()
        remove_outliers(current_smallest, 3)
        current_min = current_smallest.mean()

        # Print and save the results for each file
        print(f"File: {filename}")
        print(f"Current Max: {current_max}")
        print(f"Current Min: {current_min}")

        # Save results to a text file
        results.append([extract_nm_number(filename)/10, current_max, current_min])

        # Plot the data
        plt.figure()
        plt.plot(time_data, current_data)
        plt.plot(time_data, (current_max + time_data * 0))
        plt.plot(time_data, (current_min + time_data * 0))
        plt.xlabel("Time")
        plt.ylabel("Current")
        plt.title(f"Current vs. Time for {filename}")
        plt.show()

output_file = folder_path+"/results_mW_V.txt"
with open(output_file, 'w') as file:
    file.write("Wavelength\tMax_current\tMin_current\n")
    for result in results:
        file.write("\t".join(map(str, result)) + "\n")
