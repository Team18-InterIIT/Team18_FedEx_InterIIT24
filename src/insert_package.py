from environment import Environment
from entity import ULD, Package, Point

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
    """
    
    def __init__(self, env: Environment):
        """
        Initializes the PackageInserter with the provided Environment object.
        
        Parameters:
        env (Environment): The environment that contains ULDs and packages.
        """
        self.env = env

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
        for x in range(uld.dim.l - package.dim.l, -1, -1):
            for z in range(uld.dim.h - package.dim.h, -1, -1):
                for y in range(0, uld.dim.w - package.dim.w + 1):
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
