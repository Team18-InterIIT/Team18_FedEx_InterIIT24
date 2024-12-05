import numpy as np
from entity import ULD, Package
"""
Given a ULD and a map/dictionary called family: dict[Package, int], returns the cost

NOTE: Need to implement for special cases where the box locations are sparse

"""
family = {} 


# Shortest distance in a graph
# Many algos for pairwise shortest paths in a graph: Floyd Warshall, Johnson's Algo
def floyd_warshall(adj_matrix):
    """
    Computes pairwise shortest paths using Floyd-Warshall algorithm.

    Parameters:
        adj_matrix (numpy.ndarray): Adjacency matrix of the graph. 
            Non-edges should be represented with np.inf. [THIS IS TAKEN CARE OF IN DIST MATRIX]

    Returns:
        numpy.ndarray: Matrix where element (i, j) contains the shortest path length from node i to node j.
    """
    # Number of vertices
    n = adj_matrix.shape[0]
    
    # Initialize the distance matrix
    dist = adj_matrix.copy()
    for i in range(n):
        for j in range(n):
            if(dist[i][j] != 1):
                dist[i][j] = np.inf
    
    # Run Floyd-Warshall
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if(i == j):
                    continue
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    
    return dist

def do_cuboids_touch(cuboid1: Package, cuboid2: Package) -> bool:
    """
    Check if two cuboids touch via any of their faces.

    Parameters:
        cuboid1, cuboid2: Tuples of two points each representing the bottom-left and top-right corners.
                          Each cuboid is defined as ((x1, y1, z1), (x2, y2, z2)).
                          x1 < x2, y1 < y2, z1 < z2 for a valid cuboid.

    Returns:
        bool: True if the cuboids touch via a face; False otherwise.
    """
    # Extract coordinates
    (x1_min, y1_min, z1_min), (x1_max, y1_max, z1_max) = (cuboid1.corners[0].x, cuboid1.corners[0].y, cuboid1.corners[0].z), (cuboid1.corners[1].x, cuboid1.corners[1].y, cuboid1.corners[1].z)
    (x2_min, y2_min, z2_min), (x2_max, y2_max, z2_max) = (cuboid2.corners[0].x, cuboid2.corners[0].y, cuboid2.corners[0].z), (cuboid2.corners[1].x, cuboid2.corners[1].y, cuboid2.corners[1].z)

    # Check if cuboids touch on any face
    # A face-touch happens when one coordinate is shared, and the others overlap
    touch_x = (x1_max == x2_min or x1_min == x2_max) and (y1_min <= y2_max and y1_max >= y2_min) and (z1_min <= z2_max and z1_max >= z2_min)
    touch_y = (y1_max == y2_min or y1_min == y2_max) and (x1_min <= x2_max and x1_max >= x2_min) and (z1_min <= z2_max and z1_max >= z2_min)
    touch_z = (z1_max == z2_min or z1_min == z2_max) and (x1_min <= x2_max and x1_max >= x2_min) and (y1_min <= y2_max and y1_max >= y2_min)

    return touch_x or touch_y or touch_z


def invert_family_map(family: dict[Package, int]) -> dict[int, list[Package]]:
    """
    Inverts a map from Package -> int to a map from int -> list[Package].

    Parameters:
        family (dict[Package, int]): Dictionary mapping Package to integers.

    Returns:
        dict[int, list[Package]]: Dictionary mapping integers to lists of Package objects.
    """
    # Initialize an empty dictionary to store the inverted mapping
    inverted_map = {}

    # Populate the inverted map
    for package, family_number in family.items():
        if family_number not in inverted_map:
            inverted_map[family_number] = []
        inverted_map[family_number].append(package)

    return inverted_map


def graphFamilyCost(uld: ULD, family: dict[Package, int]) -> float:
    """
    Computes cost family cost and sums it over all families.
    
    Args: 
        uld: uld over which the cost is calcualted, family: family dictionary which maps packages to family index (which is an integer)
    
    Returns: 
        cost = sum of average pairwise shortest paths over all families
    """
    # need to construct adjacency matrix for graph
    packageArr = uld.packages # packages in the ULD
    N = len(packageArr)
    adjMatrix = np.zeros((N, N))
    for i in range(0, N):
        for j in range(0, N):
            if(i == j):
                continue
            adjMatrix[i][j] = do_cuboids_touch(packageArr[i], packageArr[j])
    
    packageToIndex = {} # takes in the package and output's it's index in the packageArr so it can be used in adjacency matrix
    for i in range(0, N): 
        packageToIndex[packageArr[i]] = i
    
    familyList = invert_family_map(family) # for a given family number, how many packages are for that
    
    pairWiseDist = floyd_warshall(adjMatrix) # pairwise distance matrix using floyed warshall algo -> O(N^3)
    
    #assuming all packages are connected as of now i.e. graph is connected, 1 component only
    # TO Do: cases where graph can be unconnected. How to deal? -> turn on sideways gravity?
    costArr = []
    for familyNumber in familyList:
        for packagesInFamily in familyList[familyNumber]:
            sum = 0
            for i in range(len(packagesInFamily)):
                for j in range(len(packagesInFamily)):
                    distance = pairWiseDist[ packageToIndex[packagesInFamily[i]] ][ packageToIndex[packagesInFamily[j]] ]
                    if(distance != np.inf): # when a box is not connected only, then ignore it. 
                        sum += distance
            sum /= 2 * len(packagesInFamily)
            costArr.append(sum)
    
    return sum(costArr)





# One way: Centroid

def centroidFamilyCost(family: dict[int, list[Package]]) -> float:
    for familyNumber in family:
        # Calculate Centroid of all the packages
        centroidX = 0.0
        centroidY = 0.0
        centroidZ = 0.0
        for packages in family[familyNumber]:
            for package in packages:
                centroidX += package.corners[0].x + package.corners[1].x
                centroidY += package.corners[0].y + package.corners[1].y
                centroidZ += package.corners[0].z + package.corners[1].z
        centroidX /= 2 * len(packages)
        centroidY /= 2 * len(packages)
        centroidZ /= 2 * len(packages)
        
        #Calculate the sum of distances frm centroid
        distSum = 0
        for packages in family[familyNumber]:
            for package in packages:
                centerX = (package.corners[0].x + package.corners[1].x) / 2
                centerY = (package.corners[0].y + package.corners[1].y) / 2
                centerZ = (package.corners[0].z + package.corners[1].z) / 2
                distSum += ((centerX - centroidX)**2 + (centerY - centroidY)**2 + (centerZ-centroidZ)**2)**0.5
        # Cost is the distance
        cost = distSum
        return cost

# Pairwise Distance Sum 

    
