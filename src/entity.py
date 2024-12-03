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

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))


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
        yield self.l
        yield self.w
        yield self.h


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
    can_be_rotated: bool
        The pacakge can only be rotated in 2/6 directions

    Methods
    -------
    volume() -> int
        Calculate the volume of the package
    """

    def __init__(self, pkg_row: list[str]):
        self.id: int = int(pkg_row[0])
        self.dim: Dim = Dim(*map(int, pkg_row[1:4]))
        self.weight: int = int(pkg_row[4])
        self.is_priority: bool = pkg_row[5] == "Priority"
        self.cost: float = float("inf") if self.is_priority else float(pkg_row[6])

        self.uld_id: int = 0
        self.corners: tuple[Point, Point] = (Point(-1, -1, -1), Point(-1, -1, -1))
        self.can_be_rotated: bool = pkg_row[7] #modify

    def new():
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
        self.can_be_rotated = pkg.can_be_rotated

    def copy(self):
        new_pkg = Package.new()
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

    def new():
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
        new_uld = ULD.new()
        new_uld.copy_from(self)
        return new_uld

    def volume(self) -> int:
        return self.dim.l * self.dim.w * self.dim.h

    def volume_utilisation(self) -> float:
        return sum(pkg.volume() for pkg in self.packages) / self.volume()

    def __repr__(self):
        return f"ULD {self.id}\t {self.dim}\t {self.weight}/{self.weight_limit}\t {'Prioritised' if self.has_priority else 'Not prioritised'}\t No. of packages: {len(self.packages)}"

    def __hash__(self):
        return hash((self.id, self.weight, len(self.packages)))

    def center_of_gravity(self):
        """
        Find the center of gravity of all the packages in the ULD
        """
        if self.weight == 0:
            return Point(self.dim.l / 2, self.dim.w / 2, self.dim.h / 2)

        x = (
            sum(
                (pkg.corners[0].x + pkg.corners[1].x) / 2 * pkg.weight
                for pkg in self.packages
            )
            / self.weight
        )
        y = (
            sum(
                (pkg.corners[0].y + pkg.corners[1].y) / 2 * pkg.weight
                for pkg in self.packages
            )
            / self.weight
        )
        z = (
            sum(
                (pkg.corners[0].z + pkg.corners[1].z) / 2 * pkg.weight
                for pkg in self.packages
            )
            / self.weight
        )
        return Point(x, y, z)

    def is_balanced(self):
        """
        Check if the ULD is balanced
        Make sure the center of gravity is within 10% of the ULD's center
        """
        cog = self.center_of_gravity()
        center_of_uld = Point(self.dim.l / 2, self.dim.w / 2, self.dim.h / 2)
        return (
            abs(cog.x - center_of_uld.x) < 0.1 * self.dim.l
            and abs(cog.y - center_of_uld.y) < 0.1 * self.dim.w
        )

    def summary(self):
        return (
            f"ULD {self.id}\n"
            f"No. of packages: {len(self.packages)}\n"
            f"Weight: {self.weight}/{self.weight_limit}\n"
            f"Volume Utilisation: {round(self.volume_utilisation() * 100, 2)}%\n"
            f"{'Balanced' if self.is_balanced() else 'Not balanced'}"
        )
