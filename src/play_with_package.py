from environment import Environment
from entity import ULD, Package, Point
from itertools import permutations
import multiprocessing
from multiprocessing import Pool
import numpy as np

class PackageInserter:
    """
    A class responsible for inserting a package into a ULD.
    
    Attributes
    ----------
    env: Environment
        The environment containing ULDs and packages.
        
    Methods
    -------
    insert_package(uld_id: int, package: Package) -> bool:
        Tries to insert the package into the specified ULD by iterating over the ULD faces.
        Methods    
    parallel_insert_package(uld_id: int, package: Package) -> bool:
        Runs insert_package_optim on all ULDs in parallel.
    initialize_grid(ULD) -> np.ndarray:
        Initializes a 3D grid for the ULD, marking occupied space (1) and free space (0).
    compute_prefix_sum(grid: np.ndarray) -> np.ndarray:
        Computes the prefix sum for the 3D grid.
    check_collision(grid: np.ndarray, x1, y1, z1, x2, y2, z2, prefix_sum: np.ndarray) -> bool:
        Checks if there is any package overlap or collision at the given coordinates using inclusion-exclusion.
    replace_package(uld_id: int, package: Package) -> bool:
        Attempts to replace a package into the specified ULD by iterating over its faces and checking collisions.
    replace_package_for_uld(uld_id, package):
        Helper method to replace a package into a ULD.
    parallel_replace_package(package: Package) -> bool:
        Attempts to insert the package into all ULDs in parallel.
    """

    def __init__(self, env: Environment):
        """
        Initializes the PackageInserter with the provided Environment object.
        
        Parameters:
        env (Environment): The environment that contains ULDs and packages.
        """
        self.env = env

    def initialize_grid(self, ULD):
        """
        Initialize a 3D grid for the ULD, marking occupied space (1) and free space (0).
        
        Parameters:
        ULD (ULD): The ULD object containing the dimensions and occupied spaces.
        
        Returns:
        np.ndarray: The initialized 3D grid.
        """
        grid = np.zeros((ULD.dim.l + 2, ULD.dim.w + 2, ULD.dim.h + 2), dtype=int)  # 0 indicates free space, 1 indicates occupied
        for pkg in self.env.packages:
            # Mark occupied space based on existing packages
            if pkg.id in [p.id for p in self.env.packages]:
                x1, y1, z1 = pkg.corners[0].x, pkg.corners[0].y, pkg.corners[0].z
                x2, y2, z2 = pkg.corners[1].x, pkg.corners[1].y, pkg.corners[1].z
                grid[x1+1:x2+2, y1+1:y2+2, z1+1:z2+2] = 1  # Mark the occupied space as 1
        return grid

    def compute_prefix_sum(self, grid: np.ndarray) -> np.ndarray:
        """
        Computes the prefix sum for the 3D grid.
        
        Parameters:
        grid (np.ndarray): The 3D grid of the ULD.
        
        Returns:
        np.ndarray: The prefix sum array.
        """
        prefix_sum = np.zeros_like(grid, dtype=int)

        # Using the inclusion-exclusion formula to fill in the prefix sum grid
        prefix_sum[1:, 1:, 1:] = grid[1:, 1:, 1:] + \
                                prefix_sum[:-1, 1:, 1:] + \
                                prefix_sum[1:, :-1, 1:] + \
                                prefix_sum[1:, 1:, :-1] - \
                                prefix_sum[:-1, :-1, 1:] - \
                                prefix_sum[:-1, 1:, :-1] - \
                                prefix_sum[1:, :-1, :-1] + \
                                prefix_sum[:-1, :-1, :-1]
        return prefix_sum

    def check_collision(self, grid: np.ndarray, x1, y1, z1, x2, y2, z2, prefix_sum: np.ndarray) -> bool:
        """
        Checks if there is any package overlap or collision at the given coordinates using inclusion-exclusion.
        
        Parameters:
        grid (np.ndarray): The 3D grid of the ULD.
        x1, y1, z1 (int): Starting coordinates of the package.
        x2, y2, z2 (int): Ending coordinates of the package.
        prefix_sum (np.ndarray): The prefix sum array.
        
        Returns:
        bool: True if the package can be inserted, False if it collides with existing packages.
        """
        x1, y1, z1, x2, y2, z2 = x1+1, y1+1, z1+1, x2+1, y2+1, z2+1
        # Get the sum of the cube from (0, 0, 0) to (x2, y2, z2)
        total = prefix_sum[x2, y2, z2]

        # Subtract areas outside the box using inclusion-exclusion
        total -= prefix_sum[x1-1, y2, z2]
        total -= prefix_sum[x2, y1-1, z2]
        total -= prefix_sum[x2, y2, z1-1]

        total += prefix_sum[x1-1, y1-1, z2]
        total += prefix_sum[x1-1, y2, z1-1]
        total += prefix_sum[x2, y1-1, z1-1]

        total -= prefix_sum[x1-1, y1-1, z1-1]

        # If the total is 1, there is exactly one package in the cube
        return total == 1

    def replace_package(self, uld_id: int, package: Package) -> bool:
        """
        Attempts to replace a package into the specified ULD by iterating over its faces and checking collisions.
        
        Parameters:
        uld_id (int): The ID of the ULD where the package is to be inserted.
        package (Package): The package to be inserted into the ULD.
        
        Returns:
        bool: True if the package was successfully inserted, False otherwise.
        """

        if package.id in [pkg.id for pkg in self.env.packages]:
            print(f"Package with id {package.id} already exists in the environment.")
            return False

        # Find the ULD by id
        uld = self.env.ULDs[uld_id - 1]
        if uld is None:
            print(f"ULD with id {uld_id} not found.")
            return False

        # Initialize grid and prefix sum for the ULD
        grid = self.initialize_grid(uld)
        prefix_sum = self.compute_prefix_sum(grid)

        possible_replacable_positions = []

        # Iterate through all possible positions and orientations
        for l, w, h in permutations([package.dim.l, package.dim.w, package.dim.h]):
            for x in range(uld.dim.l - l, -1, -1):
                for z in range(uld.dim.h - h, -1, -1):
                    for y in range(0, uld.dim.w - w + 1):
                        # Check for collision using the prefix sum method
                        if self.check_collision(grid, x, y, z, x + l, y + w, z + h, prefix_sum):
                            package.corners = (
                                Point(x, y, z),
                                Point(x + l, y + w, z + h)
                            )
                            if package.id not in [pkg.id for pkg in self.env.packages]:
                                colliding_package = self.env.find_collision(uld, (Point(x, y, z), Point(x + l, y + w, z + h)))
                                if colliding_package is not None:
                                    self.env.remove_package(colliding_package, uld)                        
                                    if self.env.add_package(package, uld, package.corners, False, True, True, True, True):
                                        possible_replacable_positions.append((package.cost, package.corners))
                                        self.env.remove_package(package, uld)
                                    self.env.add_package(colliding_package, uld, colliding_package.corners, False, True, True, True, True)
        return possible_replacable_positions

    def replace_package_for_uld(self, uld_id, package):
        lst = self.replace_package(uld_id, package)
        result = [(lst[i][0], uld_id, lst[i][1]) for i in range(len(lst))]
        return result  # Return the list for this particular ULD


    def parallel_replace_package(self, package: Package):
        """
        Attempts to insert the package into all ULDs in parallel.
        Parameters:
        package (Package): The package to be inserted into the ULDs.
        Returns:
        list: A list of boolean values indicating whether the package was inserted into each ULD.
        """

        with Pool(multiprocessing.cpu_count()) as pool:
            results = pool.starmap(self.replace_package_for_uld, 
                                   [(uld_id, package) for uld_id in range(1, len(self.env.ULDs) + 1)])

        # Flatten the list of results (since each worker returns a list of positions)
        self.replaceable_positions = [item for sublist in results for item in sublist]

        if len(self.replaceable_positions) == 0:
            print(f"Package {package.id} could not be inserted into any ULD.")
            return False

        self.replaceable_positions.sort(key=lambda x: x[0])
        colliding_package = self.env.find_collision(self.env.ULDs[self.replaceable_positions[0][1] - 1], self.replaceable_positions[0][2])
        if colliding_package is not None:
            self.env.remove_package(colliding_package, self.env.ULDs[self.replaceable_positions[0][1] - 1])
        self.env.add_package(package, self.env.ULDs[self.replaceable_positions[0][1] - 1], self.replaceable_positions[0][2], False, True, True, True, True)
        print(f"Package {package.id} inserted into ULD {self.replaceable_positions[0][1]} at position {self.replaceable_positions[0][2]}.")
        return True

    def insert_package(self, uld_id: int, package: Package) -> bool:
        """
        Attempts to insert the package into the specified ULD by iterating over its faces.
        Parameters:
        uld_id (int): The ID of the ULD where the package is to be inserted.
        package (Package): The package to be inserted into the ULD.
        Returns:
        bool: True if the package was successfully inserted, False otherwise.
        """

        if package.id in [pkg.id for pkg in self.env.packages]:
            print(f"Package with id {package.id} already exists in the environment.")
            return False

        # Find the ULD by id
        uld = self.env.ULDs[uld_id - 1]
        if uld is None:
            print(f"ULD with id {uld_id} not found.")
            return False

        # Iterate through the ULD faces and attempt to place the package
        for l, w, h in permutations([package.dim.l, package.dim.w, package.dim.h]):
            for x in range(uld.dim.l - l, -1, -1):
                for z in range(uld.dim.h - h, -1, -1):
                    for y in range(0, uld.dim.w - w + 1):
                        # Check collision at this position
                        package.corners = (
                            Point(x, y, z),
                            Point(x + package.dim.l, y + package.dim.w, z + package.dim.h)
                        )
                        if self.env.add_package(package, uld, package.corners, False, True, True, True, True):
                            print(f"Package {package.id} inserted into ULD {uld.id} at position {package.corners}.")
                            return True
        print(f"Package {package.id} could not be inserted into ULD {uld.id}.")
        return False

    def insert_package_for_uld(self, uld_id, package):
            return self.insert_package(uld_id, package)

    def parallel_insert_package(self, package: Package):
        """
        Attempts to insert the package into all ULDs in parallel.
        Parameters:
        package (Package): The package to be inserted into the ULDs.
        Returns:
        list: A list of boolean values indicating whether the package was inserted into each ULD.
        """

        # Create a pool of workers and run insert_package_optim for each ULD in parallel
        with Pool(multiprocessing.cpu_count()) as pool:
            results = pool.starmap(self.insert_package_for_uld, 
                                  [(uld_id, package) for uld_id in range(1, len(self.env.ULDs) + 1)])


        # Return the results (True or False for each ULD)
        return results