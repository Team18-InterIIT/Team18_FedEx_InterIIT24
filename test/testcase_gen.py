import random
import numpy as np
import pandas as pd

# attributes of the test case being generated
ULDs = [
    ["U1", 224, 318, 162, 2500],
    ["U2", 224, 318, 162, 2500],
    ["U3", 244, 318, 244, 2800],
    ["U4", 244, 318, 244, 2800],
    ["U5", 244, 318, 285, 3500],
    ["U6", 244, 318, 285, 3500],
]
N = 500
K = 8000


R = [3, 2, 1]  # Ratio of small to medium to large packages
volume_bins = (
    106640,
    438383,
    770126,
    1101870,
)  # lower limits for the packages in each bin (small medium large) (cm^3)

# metric used is (min(l,b,h))/volume
cubiness_mean = 0.7810441229544856
cubiness_std = 0.09815978975422106
cubiness_min = 0.5413655764387387
cubiness_max = 0.9933221725495059

length_mean = 73.5375
length_std = 19.632937230857152
length_min = 40
length_max = 110

width_mean = 76.6225
width_std = 19.854987915201107
width_min = 40
width_max = 110

height_mean = 76.6475
height_std = 20.313415045901753
height_min = 40
height_max = 110


cost_per_volume_mean = 0.000283678652493559
cost_per_volume_std = 0.00015989892637533233
cost_per_volume_min = 6.293059046320788e-05
cost_per_volume_max = 0.001093974175035868


cost_min = 60
cost_max = 170

density_mean = 0.00017962154023762764
density_std = 7.08626192952551e-05
density_min = 5.183682668469687e-05
density_max = 0.000301074604743083


percent_priority = 0.25
pkgs = []

means = [length_mean, width_mean, height_mean]
stds = [length_std, width_std, height_std]
mins = [length_min, width_min, height_min]
maxs = [length_max, width_max, height_max]

# List of dimensions
dimensions = ["length", "width", "height"]

# Create the list of dictionaries using a loop
dimension_dicts = []
for i in range(3):
    dimension_dict = {"mean": means[i], "std": stds[i], "min": mins[i], "max": maxs[i]}
    dimension_dicts.append(dimension_dict)

num_small = int((R[0] / sum(R)) * N)
num_medium = int((R[1] / sum(R)) * N)
num_high = N - num_medium - num_small

# id l w h wt type vol
for i in range(num_small):
    volume = random.randint(volume_bins[0], volume_bins[1])
    lst = [f"P-{i+1}", 0, 0, 0, 0, "", volume]
    pkgs.append(lst)
for i in range(num_medium):
    volume = random.randint(volume_bins[1], volume_bins[2])
    lst = [f"P-{i+num_small+1}", 0, 0, 0, 0, "", volume]
    pkgs.append(lst)
for i in range(num_high):
    volume = random.randint(volume_bins[2], volume_bins[3])
    lst = [f"P-{i+num_medium+num_small+1}", 0, 0, 0, 0, "", volume]
    pkgs.append(lst)

random.shuffle(pkgs)

samples = np.random.normal(loc=cubiness_mean, scale=cubiness_std, size=N)
samples_clipped = np.clip(samples, cubiness_min, cubiness_max)
for i in range(N):
    while 1:
        cubiness_sample = np.random.normal(
            loc=cubiness_mean, scale=cubiness_std, size=1
        )
        cubiness_clipped = np.clip(cubiness_sample, cubiness_min, cubiness_max)
        cubiness = cubiness_clipped[0] ** 3
        vol = pkgs[i][6]
        min_elem = int((vol * cubiness) ** (1 / 3))

        param_order = [0, 1, 2]
        random.shuffle(param_order)

        sample = np.random.uniform(
            dimension_dicts[param_order[1]]["min"],
            dimension_dicts[param_order[1]]["max"],
        )

        next_elem = int(sample)

        last_elem = vol / (min_elem * next_elem)
        last_elem = int(last_elem)

        if (
            last_elem < dimension_dicts[param_order[2]]["max"]
            and last_elem > dimension_dicts[param_order[2]]["min"]
            and min(min_elem, next_elem, last_elem) == min_elem
        ):
            break

    pkgs[i][param_order[0] + 1] = min_elem
    pkgs[i][param_order[1] + 1] = next_elem
    pkgs[i][param_order[2] + 1] = last_elem

    volume = pkgs[i][1] * pkgs[i][2] * pkgs[i][3]
    density = np.random.normal(loc=density_mean, scale=density_std, size=1)
    density = np.clip(density, density_min, density_max)
    wt = int(density[0] * vol)
    pkgs[i][4] = wt


random.shuffle(pkgs)
N_priority = int(percent_priority * N)
N_economy = N - N_priority


for i in range(N_priority):
    pkgs[i][5] = "Priority"
    pkgs[i][6] = "-"
for i in range(N_economy):
    pkgs[i + N_priority][5] = "Economy"
    vol = pkgs[i + N_priority][1] * pkgs[i + N_priority][2] * pkgs[i + N_priority][3]

    cost = 0
    while cost < cost_min or cost > cost_max:
        cost_per_volume = np.random.normal(
            loc=cost_per_volume_mean, scale=cost_per_volume_std, size=1
        )
        cost_per_volume = np.clip(
            cost_per_volume, cost_per_volume_min, cost_per_volume_max
        )
        cost = int(cost_per_volume[0] * vol)

    pkgs[i + N_priority][6] = cost


columns = [
    "Package Identifier",
    "Length (cm)",
    "Width (cm)",
    "Height (cm)",
    "Weight (kg)",
    "Type (P/E)",
    "Cost of Delay",
]

# Create DataFrame
df = pd.DataFrame(pkgs, columns=columns)
df.sort_values(by="Package Identifier", inplace=True, key=lambda x: x.str.split("-").str[1].astype(int))

with open("output.txt", "w") as file:
    # Write the value of K
    file.write(f"{K}\n")

    # Write an empty line
    file.write("\n")

    # Write the header
    file.write("ULD Identifier,Length (cm),Width (cm),Height (cm),Weight Limit (kg)\n")

    # Write the contents of the list of lists ULDs line by line
    for uld in ULDs:
        file.write(",".join(map(str, uld)) + "\n")

    # Add a final newline (optional)
    file.write("\n")

df.to_csv("output.txt", mode="a", sep=",", index=False)
