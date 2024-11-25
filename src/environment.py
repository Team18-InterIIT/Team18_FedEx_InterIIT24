import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from entity import ULD, Package, Point
from matplotlib.animation import FuncAnimation


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

    axes_id = {"length": 0, "width": 1, "height": 2}

    def __init__(self, K, uld_list: list[list[str]], pkg_list: list[list[str]]):
        self.K = K

        self.packages: list[Package] = list()
        for pkg_data_row in pkg_list:
            self.packages.append(Package(pkg_data_row))

        self.ULDs: list[ULD] = list()
        for uld_data_row in uld_list:
            self.ULDs.append(ULD(uld_data_row))

        self.pkg_addition_order = []

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

        self.pkg_addition_order.append(pkg.id)

        pkg.uld_id = uld.id
        pkg.corners = corners

        uld.packages.append(pkg)
        uld.weight += pkg.weight
        uld.has_priority = uld.has_priority or pkg.is_priority

        return True

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
        plt.close()

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

    def animate(self):
        """
        Animate the process of adding packages to the ULDs
        """

        fig = plt.figure(figsize=(15, 10))
        num_ULDs = len(self.ULDs)
        rows = 2
        cols = (num_ULDs + 1) // 2
        axes = []

        for i, uld in enumerate(self.ULDs):
            ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
            ax.set_xlabel("Length")
            ax.set_ylabel("Width")
            ax.set_zlabel("Height")
            ax.set_xlim(0, uld.dim.l)
            ax.set_ylim(0, uld.dim.w)
            ax.set_zlim(0, uld.dim.h)
            axes.append(ax)

        def update(frame):
            for ax, uld in zip(axes, self.ULDs):
                ax.cla()
                ax.set_xlabel("Length")
                ax.set_ylabel("Width")
                ax.set_zlabel("Height")
                ax.set_xlim(0, uld.dim.l)
                ax.set_ylim(0, uld.dim.w)
                ax.set_zlim(0, uld.dim.h)

            uld_data = {uld.id: (0, 0, uld.weight_limit, 0) for uld in self.ULDs}

            for pkg_id in self.pkg_addition_order[: frame + 1]:
                pkg = next(pkg for pkg in self.packages if pkg.id == pkg_id)
                uld = next(uld for uld in self.ULDs if uld.id == pkg.uld_id)
                uld_data[uld.id] = (
                    uld_data[uld.id][0] + 1,
                    uld_data[uld.id][1] + pkg.weight,
                    uld_data[uld.id][2],
                    uld_data[uld.id][3] + pkg.volume() / uld.volume(),
                )
                summary = f"ULD {uld.id}\nNo. of packages: {uld_data[uld.id][0]}\nWeight: {uld_data[uld.id][1]}/{uld_data[uld.id][2]}\nVolume Utilisation: {round(uld_data[uld.id][3] * 100, 3)}%"
                ax = axes[self.ULDs.index(uld)]
                ax.set_title(
                    summary,
                    loc="left",
                    fontdict={"fontsize": 7, "fontfamily": "monospace"},
                )

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

        frames_to_skip = 1
        frames = range(0, len(self.pkg_addition_order), frames_to_skip)

        FuncAnimation(
            fig,
            update,
            frames=frames,
            repeat=False,
        )
        plt.tight_layout()
        fig.subplots_adjust(top=0.9)
        plt.show()
        plt.close()
