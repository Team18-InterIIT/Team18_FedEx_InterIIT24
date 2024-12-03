import numpy as np
import csv
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import parser
import random
import math
"""
Stand Alone File that create the clusters based on dimensions(can be made randomly too) and makes families randomly. 
"""


def clustering(K,uldList,pList, num_clusters, family_creation):
    pack = []
    package_ids = []  # To store package IDs
    
    # Ensure you are appending the correct items
    for pkg in pList:
        # Assuming pkg is a list where [0] is the package ID (e.g., 'P1'), and [1], [2], [3] are the dimensions
        pack.append([int(pkg[1]), int(pkg[2]), int(pkg[3])])  # Width, Height, Depth
        package_ids.append(pkg[0])    
    boxes = np.array(pack)

    # If boxes is empty, exit the function early
    if boxes.size == 0:
        print("No valid packages to cluster.")
        return
    
    #Clustering boxes based on their dimensions
    def cluster_boxes(boxes, num_clusters=2):
        kmeans = KMeans(n_clusters=num_clusters, random_state=0)
        kmeans.fit(boxes)
        return kmeans.labels_, kmeans.cluster_centers_

    # Perform clustering
    labels, centers = cluster_boxes(boxes, num_clusters)

    # Visualize the clusters
    def visualize_clusters(boxes, labels, centers):
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')

        # Plot each box with a color corresponding to its cluster
        for i, label in enumerate(np.unique(labels)):
            cluster_boxes = boxes[labels == label]
            ax.scatter(cluster_boxes[:, 0], cluster_boxes[:, 1], cluster_boxes[:, 2],
                    label=f'Cluster {label + 1}', alpha=0.8, s=100)

        # Plot the cluster centers
        ax.scatter(centers[:, 0], centers[:, 1], centers[:, 2], c='black', label='Centers', marker='X', s=200)

        # Labels and legend
        ax.set_xlabel('Width')
        ax.set_ylabel('Height')
        ax.set_zlabel('Depth')
        ax.set_title('3D Box Clustering')
        ax.legend()
        plt.show()

    # visualization function
    # visualize_clusters(boxes, labels, centers)

    # Mapping Package IDs to Clusters
    package_cluster_mapping = {}
    for idx, label in enumerate(labels):
        package_cluster_mapping[package_ids[idx]] = label
    
    # Print the mapping of package IDs to clusters
    
    
    for pack in pList:
        for pack_id in package_cluster_mapping.keys():
            # print("pack[0][2:] = "pack[0][2:])
            if pack[0]== pack_id:
                pack.append(package_cluster_mapping[pack_id].item())
        pack[0] = f"P-{pack[0]}"

# List of lists (each list is a row)
    if family_creation:
        for pkg in pList:
            pkg.append(0 if random.random() < 0.5 else random.randrange(1,family_creation))
    # Specify the file path
    file_path = f'test/data_cluster{num_clusters}_fam{family_creation}.txt'

    # Open the CSV file in append mode (use 'w' to overwrite)
    with open(file_path, mode='w', newline='') as file:
    
        writer = csv.writer(file)
        
        # Write all rows at once
        writer.writerow([K])
        writer.writerows([[],["ULD Identifier","Length (cm)","Width (cm)","Height (cm)","Weight Limit (kg)"]])
        writer.writerows(uldList)
        writer.writerows([[],["Package Identifier","Length (cm)","Width (cm)","Height (cm)","Weight (kg)","Type (P/E)","Cost of Delay","Clusterid"]])
        writer.writerows(pList)

    print("Data added to CSV successfully!")

    
# return package_cluster_mapping
test_file = "test/Challenge_FedEx.txt"
parser = parser.Parser(test_file)
K = parser.get_K()
uld_list = parser.get_uld_list()
for uld in uld_list:
    uld[0]=str(f"U{uld[0]}")
pkg_list = parser.get_pkg_list()

num_clusters=3
family_creation = 2
clustering(K,uld_list,pkg_list,num_clusters,family_creation)