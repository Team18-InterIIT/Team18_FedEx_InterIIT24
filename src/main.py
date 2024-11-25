import itertools

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import parser

axes_id = {"length": 0, "width": 1, "height": 2}


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
        return f"({self.x}, {self.y}, {self.z})"


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

    Methods
    -------
    volume() -> int
        Calculate the volume of the package
    """

    def __init__(self, pkg_row: list[str]):
        self.id: int = int(pkg_row[0])
        self.dim: Dim = Dim(int(pkg_row[1]), int(pkg_row[2]), int(pkg_row[3]))
        self.weight: int = int(pkg_row[4])
        self.is_priority: bool = pkg_row[5] == "Priority"
        self.cost: float = float("inf") if self.is_priority else float(pkg_row[6])

        self.uld_id: int = 0
        self.corners: tuple[Point, Point] = (Point(-1, -1, -1), Point(-1, -1, -1))

    def volume(self):
        return self.dim.l * self.dim.w * self.dim.h

    def __repr__(self):
        return f"Package {self.id}\t {self.dim}\t {self.weight}\t {self.is_priority}\t {self.cost}\t {self.uld_id}\t {self.corners}"


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
        self.dim: Dim = Dim(int(uld_row[1]), int(uld_row[2]), int(uld_row[3]))
        self.weight_limit: int = int(uld_row[4])

        self.has_priority: bool = False
        self.weight: int = 0
        self.packages: list[Package] = list()

    def volume(self):
        return self.dim.l * self.dim.w * self.dim.h

    def __repr__(self):
        return f"ULD {self.id}\t {self.dim}\t {self.weight}/{self.weight_limit}\t {"Prioritised" if self.has_priority else "Not prioritised"}\t No. of packages: {len(self.packages)}"

    def summary(self):
        return (
            f"ULD {self.id}\n"
            f"No. of packages: {len(self.packages)}\n"
            f"Weight: {self.weight}/{self.weight_limit}\n"
            f"Volume Utilisation: {round(sum(pkg.volume() for pkg in self.packages) / self.volume() * 100, 3)}%\n"
        )


class Environment:
    """
    Represents the environment

    Attributes
    ----------
    K: int
        The cost of putting a priority package in a ULD that is not prioritised
    packages: list[Package]
        The list of packages
    ULDs: list[ULD]
        The list of ULDs

    Methods
    -------
    check_collision(uld, corners_to_check) -> bool
        Check if the package with the given coordinates would
        collide with any other package in the ULD
    check_weight_limit(uld, pkg_weight) -> bool
        Check if the package with the given weight would
        exceed the weight limit of the ULD
    add_package(pkg, uld, corners, collision_check, weight_limit_check,
                floating_check, stability_check, fragility_check) -> bool
        Add a package to the ULD at the given coordinates
        taking into account various constraints
    pack_to_ULD(pkg, uld) -> bool
        Pack the package to the ULD
    pack() -> None
        Pack the packages to the ULDs
    """

    def __init__(self, K, uld_list: list[list[str]], pkg_list: list[list[str]]):
        self.K = K

        self.packages: list[Package] = list()
        for pkg_data_row in pkg_list:
            self.packages.append(Package(pkg_data_row))

        self.ULDs: list[ULD] = list()
        for uld_data_row in uld_list:
            self.ULDs.append(ULD(uld_data_row))

    def check_collision(self, uld: ULD, corners_to_check: tuple[Point, Point]):
        """
        Check if the package with the given coordinates will collide with any other package in the ULD

        Returns **True if collision is detected, False otherwise**
        """
        if (
            corners_to_check[0].x < 0
            or corners_to_check[0].y < 0
            or corners_to_check[0].z < 0
            or corners_to_check[1].x > uld.dim.l
            or corners_to_check[1].y > uld.dim.w
            or corners_to_check[1].z > uld.dim.h
        ):
            return True

        for existing_pkg in uld.packages:
            if (
                corners_to_check[0].x < existing_pkg.corners[1].x
                and corners_to_check[1].x > existing_pkg.corners[0].x
                and corners_to_check[0].y < existing_pkg.corners[1].y
                and corners_to_check[1].y > existing_pkg.corners[0].y
                and corners_to_check[0].z < existing_pkg.corners[1].z
                and corners_to_check[1].z > existing_pkg.corners[0].z
            ):
                return True

        return False

    def check_weight_limit(self, uld: ULD, pkg_weight: int):
        """
        Check if the package with the given weight will exceed the weight limit of the ULD

        Returns **True if weight limit is exceeded, False otherwise**
        """
        return uld.weight + pkg_weight > uld.weight_limit

    def add_package(
        self,
        pkg: Package,
        uld: ULD,
        corners: tuple[Point, Point],
        collision_check: bool = True,
        weight_limit_check: bool = True,
        floating_check: bool = True,
        stability_check: bool = True,
        fragility_check: bool = True,
    ):
        """
        Add a package to the ULD at the given coordinates,
        taking into account various constraints

        Returns **True if the package is successfully added, False otherwise**
        """
        if collision_check and self.check_collision(uld, corners):
            return False

        if weight_limit_check and self.check_weight_limit(uld, pkg.weight):
            return False

        pkg.uld_id = uld.id
        pkg.corners = corners

        uld.packages.append(pkg)
        uld.weight += pkg.weight
        uld.has_priority = uld.has_priority or pkg.is_priority

        return True

    def pivot_package(self, pkg: Package, uld: ULD, pivot: Point) -> bool:
        for l_inc, b_inc, h_inc in itertools.permutations(
            [pkg.dim.l, pkg.dim.w, pkg.dim.h]
        ):
            if self.add_package(
                pkg,
                uld,
                corners=(
                    pivot,
                    Point(
                        pivot.x + l_inc,
                        pivot.y + b_inc,
                        pivot.z + h_inc,
                    ),
                ),
            ):
                return True

        return False

    def pack_to_ULD(self, pkg: Package, uld: ULD) -> bool:
        """
        Pack the package to the ULD
        """
        if not uld.packages:
            return self.pivot_package(pkg, uld, Point(0, 0, 0))

        for axis in range(0, 3):
            for existing_pkg in uld.packages:
                pivot = Point(0, 0, 0)
                l, w, h = existing_pkg.dim.l, existing_pkg.dim.w, existing_pkg.dim.h
                if axis == axes_id["length"]:
                    pivot = Point(
                        existing_pkg.corners[0].x + l,
                        existing_pkg.corners[0].y,
                        existing_pkg.corners[0].z,
                    )
                elif axis == axes_id["width"]:
                    pivot = Point(
                        existing_pkg.corners[0].x,
                        existing_pkg.corners[0].y + w,
                        existing_pkg.corners[0].z,
                    )
                elif axis == axes_id["height"]:
                    pivot = Point(
                        existing_pkg.corners[0].x,
                        existing_pkg.corners[0].y,
                        existing_pkg.corners[0].z + h,
                    )

                if self.pivot_package(pkg, uld, pivot):
                    return True

        return False

    def pack(self):
        """
        Add packages to the ULDs
        """
        sorted_ULDs = sorted(self.ULDs, key=lambda uld: uld.volume(), reverse=True)
        sorted_pkgs = sorted(
            self.packages,
            key=lambda pkg: pkg.cost**1.5 / pkg.volume(),
            reverse=True,
        )
        for uld in sorted_ULDs:
            for pkg in sorted_pkgs:
                if pkg.uld_id == 0:
                    self.pack_to_ULD(pkg, uld)

        for pkg in self.packages:
            if pkg.uld_id == 0:
                for uld in self.ULDs:
                    self.pack_to_ULD(pkg, uld)

    def cost(
        self,
        priority_check: bool = True,
        collision_check: bool = True,
        weight_limit_check: bool = True,
    ) -> tuple[float, float]:
        """
        Calculate the cost of the current packing

        Returns a tuple of the delay cost and the priority cost
        Returns (inf, inf) if any constraint is violated
        """
        if collision_check:
            for uld in self.ULDs:
                sorted_pkgs = sorted(uld.packages, key=lambda p: p.corners[0].x)
                active = []

                for pkg in sorted_pkgs:
                    active = [p for p in active if p.corners[1].x > pkg.corners[0].x]

                    for other in active:
                        if (
                            pkg.corners[0].y < other.corners[1].y
                            and pkg.corners[1].y > other.corners[0].y
                            and pkg.corners[0].z < other.corners[1].z
                            and pkg.corners[1].z > other.corners[0].z
                        ):
                            print(f"Collision detected between {pkg.id} and {other.id}")
                            return float("inf"), float("inf")

                        active.append(pkg)

        priority_cost = 0
        for uld in self.ULDs:
            if weight_limit_check and uld.weight > uld.weight_limit:
                print("ULD weight limit exceeded")
                return float("inf"), float("inf")
            if uld.has_priority:
                priority_cost += self.K

        delay_cost = 0
        for pkg in self.packages:
            if pkg.uld_id == 0:
                if pkg.is_priority:
                    if priority_check:
                        print("Priority package not placed")
                        return float("inf"), float("inf")
                else:
                    delay_cost += pkg.cost

        return delay_cost, priority_cost

    def plot(self):
        """
        Plot the packages in the ULDs
        """
        fig = plt.figure(figsize=(15, 10))
        num_ULDs = len(self.ULDs)
        rows = 2
        cols = (num_ULDs + 1) // 2

        for i, uld in enumerate(self.ULDs):
            ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
            for pkg in uld.packages:
                x = [pkg.corners[0].x, pkg.corners[1].x]
                y = [pkg.corners[0].y, pkg.corners[1].y]
                z = [pkg.corners[0].z, pkg.corners[1].z]

                points = (
                    ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)),
                    ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
                    ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
                    ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
                    ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),
                    ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
                )
                verts = [
                    [(x[p[0]], y[p[1]], z[p[2]]) for p in point] for point in points
                ]

                color = "lightblue" if not pkg.is_priority else "cyan"

                ax.add_collection3d(
                    Poly3DCollection(
                        verts,
                        facecolors=color,
                        linewidths=1,
                        edgecolors="r",
                        alpha=0.2,
                    )
                )

            ax.set_xlabel("Length")
            ax.set_ylabel("Width")
            ax.set_zlabel("Height")

            ax.set_xlim(0, uld.dim.l)
            ax.set_ylim(0, uld.dim.w)
            ax.set_zlim(0, uld.dim.h)

            ax.set_title(uld.summary())

        plt.tight_layout()
        plt.show()

    def summary(self):
        """
        Print a summary of the packing
        """
        delay_cost, priority_cost = self.cost()

        for uld in self.ULDs:
            print(uld.summary())
            print("-" * 50)

        packages = set(pkg for pkg in self.packages)
        placed = set(pkg for pkg in self.packages if pkg.uld_id != 0)
        not_placed = packages - placed

        priority_ULDs = set(uld for uld in self.ULDs if uld.has_priority)
        priority_pkgs = set(pkg for pkg in self.packages if pkg.is_priority)
        priority_pkgs_placed = priority_pkgs & placed

        print(
            f"Number of packages placed: {len(placed)}\nNumber of packages not placed: {len(not_placed)}"
            f"\nNumber of ULDs that are priority: {len(priority_ULDs)}"
            f"\nPercentage volume filled: {round(sum(pkg.volume() for pkg in placed) / sum(uld.volume() for uld in self.ULDs) * 100, 3)}%"
            f"\nPercentage of non-priority packages placed: {round((len(placed) - len(priority_pkgs_placed)) / (len(packages) - len(priority_pkgs)) * 100, 3)}%"
            f"\nCost ==> Priority: {priority_cost} + Delay: {delay_cost} = {priority_cost + delay_cost}"
        )


K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

env = Environment(K, uld_list, pkg_list)
env.pack()
env.plot()
env.summary()
