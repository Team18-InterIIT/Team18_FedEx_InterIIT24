class Point:
    """
    Represents a point in 3D space

    Attributes
    ----------
    x: int
    y: int
    z: int
    """

    def __init__(self, x: int, y: int, z: int):
        self.x: int = x
        self.y: int = y
        self.z: int = z

    def __repr__(self):
        return f"Point({self.x}, {self.y}, {self.z})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def dist(self,point: 'Point'=None): 
        if point is None:
            point=Point(0,0,0)
        return ((self.x-point.x)**2+(self.y-point.y)**2+(self.z-point.z)**2)**0.5

class Dim:
    """
    Represents the dimensions of a package or ULD

    Attributes
    ----------
    l: int
        Length (along x-axis)
    w: int
        Width (along y-axis)
    h: int
        Height (along z-axis)
    """

    def __init__(self, length: int, width: int, height: int):
        self.l: int = length
        self.w: int = width
        self.h: int = height

    def __repr__(self):
        return f"{self.l}x{self.w}x{self.h}"

    def __iter__(self):
        # Makes the Dim object iterable (e.g., (length, width, height))
        return iter((self.l, self.w, self.h))


class Package:
    """Represents a package

    Attributes
    ----------
    id: int
        The unique identifier of the package
    dim: Dim
        The dimensions of the package
    weight: int
        The weight of the package
    is_priority: bool
        Whether the package is prioritised
    cost: float
        The cost of delay for the package
    uld_id: int
        The identifier of the ULD in which the package is placed
    corners: tuple[Point, Point]
        The coordinates of the corners of the package in the ULD
    cluster_id:
        All objects of the same cluster needto be packed in same ULD as much as possible. 
    cluster_thresh:
        the Minimum "Cluster Union Ratio (CUR)" for each ULD. CUR = max(frequncy of clusterid)/total packages. 
    family_id:
        All objects of the same family must be packed adjecent to each other as much as possible.
    family_thresh_dist:
        The maximum allowable distance between two packages of same family.  
    

    Methods
    -------
    volume() -> int
        Calculate the volume of the package
    """

    def __init__(self, pkg_row: list[str],cluster_thresh=0.6,family_thresh_dist=5):
        self.id: int = int(pkg_row[0])
        self.dim: Dim = Dim(*map(int, pkg_row[1:4]))
        self.weight: int = int(pkg_row[4])
        self.is_priority: bool = pkg_row[5] == "Priority"
        self.cost: float = float("inf") if self.is_priority else float(pkg_row[6])


        self.uld_id: int = 0
        self.corners: tuple[Point, Point] = (Point(-1, -1, -1), Point(-1, -1, -1))
        if(len(pkg_row)>7):
            self.cluster_id=str(pkg_row[7])
        else:
            self.cluster_id='0'
        
        self.cluster_thresh = cluster_thresh

        if(len(pkg_row)>8):
            self.family_id=str(pkg_row[8])
        else:
            self.family_id='0'

        self.family_threshold_distance=family_thresh_dist


    def new(self):
        return Package(["0", "0", "0", "0", "0", "Economy", "0"])

    def reset(self):
        self.uld_id = 0
        self.corners = (Point(-1, -1, -1), Point(-1, -1, -1))

    def copy_from(self, pkg):
        self.id = pkg.id
        self.dim = pkg.dim
        self.weight = pkg.weight
        self.is_priority = pkg.is_priority
        self.cost = pkg.cost
        self.uld_id = pkg.uld_id
        self.corners = pkg.corners

    def copy(self):
        new_pkg = self.new()
        new_pkg.copy_from(self)
        return new_pkg

    def volume(self):
        return self.dim.l * self.dim.w * self.dim.h

    def get_corners(self):
        x_min, y_min, z_min = self.corners[0].x, self.corners[0].y, self.corners[0].z
        x_max, y_max, z_max = self.corners[1].x, self.corners[1].y, self.corners[1].z
        return [
            Point(x_min, y_min, z_min),
            Point(x_min, y_min, z_max),
            Point(x_min, y_max, z_min),
            Point(x_min, y_max, z_max),
            Point(x_max, y_min, z_min),
            Point(x_max, y_min, z_max),
            Point(x_max, y_max, z_min),
            Point(x_max, y_max, z_max),
        ]

    def __repr__(self):
        return f"Package {self.id}\t {self.dim}\t {self.weight}\t {self.is_priority}\t {self.cost}\t {self.uld_id}\t {self.corners}"

    def __hash__(self):
        return hash((self.id, self.uld_id, *self.corners))

    def min_dist(self, pkg: 'Package'):
        #Returns the minimum distance between 2 boxes (comparing corners). 
        distance= float('inf')
        for corner1 in self.get_corners():
            for corner2 in pkg.get_corners():
                if corner1.dist(corner2)<distance:
                    distance = corner1.dist(corner2)
        return distance
class ULD:
    """
    Represents a ULD

    Attributes
    ----------
    id: int
        The unique identifier of the ULD
    dim: Dim
        The dimensions of the ULD
    weight_limit: int
        The weight limit of the ULD
    has_priority: bool
        Whether the ULD contains any prioritised packages
    weight: int
        The total weight of the packages in the ULD
    packages: list[Package]
        The packages packed in the ULD
    cluster_dict:
        {'cluster_id' : int } -- a record of how many packets of a given clusterid are in the ULD

    family_dict
        {'family_id' : [Package,...]} -- record of the list of same-family packages placed next to each other in a ULD. List of Package Class Objects. 
    Methods
    -------
    volume() -> int
        Calculate the volume of the ULD
    summary() -> str
        Return a summary of the ULD
    """

    def __init__(self, uld_row: list[str]):
        self.id: int = int(uld_row[0])
        self.dim: Dim = Dim(*map(int, uld_row[1:4]))
        self.weight_limit: int = int(uld_row[4])

        self.has_priority: bool = False
        self.weight: int = 0
        self.packages: list[Package] = list()
        self.cluster_dict = {} 
        self.family_dict={} 
    def new(self):
        return ULD(["0", "0", "0", "0", "0"])

    def reset(self):
        self.has_priority = False
        self.weight = 0
        self.packages = []

    def copy_from(self, uld):
        self.id = uld.id
        self.dim = uld.dim
        self.weight_limit = uld.weight_limit
        self.has_priority = uld.has_priority
        self.weight = uld.weight
        self.packages = [pkg.copy() for pkg in uld.packages]

    def copy(self):
        new_uld = self.new()
        new_uld.copy_from(self)
        return new_uld

    def volume(self) -> int:
        return self.dim.l * self.dim.w * self.dim.h

    def volume_utilisation(self) -> float:
        return sum(pkg.volume() for pkg in self.packages) / self.volume()

    def __repr__(self):
        return f'ULD {self.id}\t {self.dim}\t {self.weight}/{self.weight_limit}\t {"Prioritised" if self.has_priority else "Not prioritised"}\t No. of packages: {len(self.packages)}'

    def summary(self):
        return (
            f"ULD {self.id}\n"
            f"No. of packages: {len(self.packages)}\n"
            f"Weight: {self.weight}/{self.weight_limit}\n"
            f"Volume Utilisation: {round(sum(pkg.volume() for pkg in self.packages) / self.volume() * 100, 3)}%\n"
        )
