import parser
import itertools
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

axes_id = {"length": 0, "breadth": 1, "height": 2}

class Dim:
    def __init__(self, length: int, width: int, height: int):
        self.l: int = length
        self.w: int = width
        self.h: int = height


class Package:
    def __init__(self, pkg_row: list[str]):
        # id, length, width, hegiht, wt, type, cost (strings)
        self.id: int = int(pkg_row[0])
        self.dim: Dim = Dim(int(pkg_row[1]), int(pkg_row[2]), int(pkg_row[3]))
        self.weight: int = int(pkg_row[4])
        self.is_priority: bool = pkg_row[5] == "Priority"
        self.cost: float = float("inf") if self.is_priority else float(pkg_row[6])

        self.uld: int = 0
        self.coords: tuple[tuple] = ((-1, -1, -1), (-1, -1, -1))

    def get_volume(self):
        return self.dim.l * self.dim.w * self.dim.h

    def __repr__(self):
        return f"Package {self.id}\t {self.dim.l}x{self.dim.w}x{self.dim.h}\t {self.weight}\t {self.is_priority}\t {self.cost}\t {self.uld}\t {self.coords}"


class ULD:
    def __init__(self, uld_row: list[str]):
        self.id: int = int(uld_row[0])
        self.dim: Dim = Dim(int(uld_row[1]), int(uld_row[2]), int(uld_row[3]))
        self.weight_limit: int = int(uld_row[4])

        self.has_priority: bool = False
        self.weight: int = 0
        self.packages: list[Package] = list()

    def get_volume(self):
        l, b, h = self.dim.l, self.dim.w, self.dim.h
        return l * b * h

    def __repr__(self):
        return f"ULD {self.id}, {self.dim.l}x{self.dim.w}x{self.dim.h}, {self.weight}/{self.weight_limit}, {self.get_volume()}"


class Environment:
    def __init__(self, K, uld_list: list[list[str]], pkg_list: list[list[str]]):
        self.K = K

        self.packages: list[Package] = list()
        for pkg_data_row in pkg_list:
            self.packages.append(Package(pkg_data_row))

        self.ULDs: list[ULD] = list()
        for uld_data_row in uld_list:
            self.ULDs.append(ULD(uld_data_row))

    def check_collision(self, uld_id: int, coords_to_check: tuple[tuple]):
        for curr_pkg in self.ULDs[uld_id - 1].packages:
            if (
                coords_to_check[0][0] < curr_pkg.coords[1][0]
                and coords_to_check[1][0] > curr_pkg.coords[0][0]
                and coords_to_check[0][1] < curr_pkg.coords[1][1]
                and coords_to_check[1][1] > curr_pkg.coords[0][1]
                and coords_to_check[0][2] < curr_pkg.coords[1][2]
                and coords_to_check[1][2] > curr_pkg.coords[0][2]
            ):
                return True

        # Check collisions between uld and coords_to_check
        if (
            coords_to_check[0][0] < 0
            or coords_to_check[0][1] < 0
            or coords_to_check[0][2] < 0
            or coords_to_check[1][0] > self.ULDs[uld_id - 1].dim.l
            or coords_to_check[1][1] > self.ULDs[uld_id - 1].dim.w
            or coords_to_check[1][2] > self.ULDs[uld_id - 1].dim.h
        ):
            return True

        return False

    def check_weight_limit(self, uld_id: int, pkg_weight: int):
        return (
            self.ULDs[uld_id - 1].weight + pkg_weight
            > self.ULDs[uld_id - 1].weight_limit
        )

    def add_package(
        self,
        pkg_id: int,
        uld_id: int,
        coords: tuple[tuple],
        collision_check: bool = True,
        weight_limit_check: bool = True,
        floating_check: bool = True,
        stability_check: bool = True,
        fragility_check: bool = True,
    ):
        if collision_check and self.check_collision(uld_id, coords):
            return False

        if weight_limit_check and self.check_weight_limit(
            uld_id, self.packages[pkg_id - 1].weight
        ):
            return False

        pkg = self.packages[pkg_id - 1]
        uld = self.ULDs[uld_id - 1]

        pkg.uld = uld_id
        pkg.coords = coords

        uld.packages.append(pkg)
        uld.weight += pkg.weight
        uld.has_priority = uld.has_priority or pkg.is_priority

        return True

    def try_all_rotations(self, pkg_id, uld_id, pivot):
        pkg = self.packages[pkg_id - 1]
        for l_inc, b_inc, h_inc in itertools.permutations(
            [pkg.dim.l, pkg.dim.w, pkg.dim.h]
        ):
            if self.add_package(
                pkg_id,
                uld_id,
                coords=(
                    pivot,
                    (
                        pivot[0] + l_inc,
                        pivot[1] + b_inc,
                        pivot[2] + h_inc,
                    ),
                ),
            ):
                return True
        return False

    def pack_to_bin(self, uld_id, pkg_id):
        uld = self.ULDs[uld_id - 1]
        pkg = self.packages[pkg_id - 1]

        fitted = False

        if not uld.packages:
            self.try_all_rotations(pkg_id, uld_id, (0, 0, 0))
            return

        for axis in range(0, 3):
            items_in_bin = uld.packages

            for ib in items_in_bin:
                pivot = (0, 0, 0)
                l, b, h = ib.dim.l, ib.dim.w, ib.dim.h
                if axis == axes_id["length"]:
                    pivot = (ib.coords[0][0] + l, ib.coords[0][1], ib.coords[0][2])
                elif axis == axes_id["breadth"]:
                    pivot = (ib.coords[0][0], ib.coords[0][1] + b, ib.coords[0][2])
                elif axis == axes_id["height"]:
                    pivot = (ib.coords[0][0], ib.coords[0][1], ib.coords[0][2] + h)

                if self.try_all_rotations(pkg_id, uld_id, pivot):
                    fitted = True
                    break

            if fitted:
                break

    def pack(self):
        sorted_ULDs = sorted(
            self.ULDs, key=lambda uld: uld.get_volume(), reverse=True
        )
        sorted_pkgs = sorted(
            self.packages, key=lambda pkg: (pkg.cost)**1.5 / pkg.get_volume(), reverse=True
        )
        for uld in sorted_ULDs:
            for pkg in sorted_pkgs:
                if pkg.uld == 0:
                    self.pack_to_bin(uld.id, pkg.id)

    def plot(self):
        for uld in self.ULDs:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
            for pkg in uld.packages:
                x = [pkg.coords[0][0], pkg.coords[1][0]]
                y = [pkg.coords[0][1], pkg.coords[1][1]]
                z = [pkg.coords[0][2], pkg.coords[1][2]]

                verts = [
                    [
                        (x[0], y[0], z[0]),
                        (x[1], y[0], z[0]),
                        (x[1], y[1], z[0]),
                        (x[0], y[1], z[0]),
                    ],
                    [
                        (x[0], y[0], z[1]),
                        (x[1], y[0], z[1]),
                        (x[1], y[1], z[1]),
                        (x[0], y[1], z[1]),
                    ],
                    [
                        (x[0], y[0], z[0]),
                        (x[1], y[0], z[0]),
                        (x[1], y[0], z[1]),
                        (x[0], y[0], z[1]),
                    ],
                    [
                        (x[0], y[1], z[0]),
                        (x[1], y[1], z[0]),
                        (x[1], y[1], z[1]),
                        (x[0], y[1], z[1]),
                    ],
                    [
                        (x[0], y[0], z[0]),
                        (x[0], y[1], z[0]),
                        (x[0], y[1], z[1]),
                        (x[0], y[0], z[1]),
                    ],
                    [
                        (x[1], y[0], z[0]),
                        (x[1], y[1], z[0]),
                        (x[1], y[1], z[1]),
                        (x[1], y[0], z[1]),
                    ],
                ]
                ax.add_collection3d(
                    Poly3DCollection(
                        verts,
                        facecolors="lightblue",
                        linewidths=1,
                        edgecolors="r",
                        alpha=0.25,
                    )
                )

            ax.set_xlabel("Length")
            ax.set_ylabel("Breadth")
            ax.set_zlabel("Height")

            plt.show()

        plt.close()

    def summary(self):
        # Number of packages in each ULD, with volume occupied percentage and weight filled percentage
        for uld in self.ULDs:
            print(f"ULD {uld.id}")
            print(f"  Packages: {len(uld.packages)}")
            print(f"  Volume: {sum(pkg.get_volume() for pkg in uld.packages)}/{uld.get_volume()}")
            print(f" Percentage Volume: {sum(pkg.get_volume() for pkg in uld.packages) / uld.get_volume() * 100}%")
            print(f"  Weight: {uld.weight}/{uld.weight_limit}")
            print(f" Percentage Weight: {uld.weight / uld.weight_limit * 100}%")
            print(f"  Priority: {uld.has_priority}")
            print()

        # Number of ULDs that are priority
        priority_ULDs = [uld for uld in self.ULDs if uld.has_priority]
        total_priority_cost = len(priority_ULDs) * K
        
        # Number of packages not placed, and sum of costs of packages not placed, sum of volume not filled
        not_placed = [pkg for pkg in self.packages if pkg.uld == 0]
        placed = [pkg for pkg in self.packages if pkg.uld != 0]
        priority_pkgs_placed = [pkg for pkg in placed if pkg.is_priority]
        priority_pkgs = [pkg for pkg in self.packages if pkg.is_priority]
        print(f"Number of packages not placed: {len(not_placed)}")
        print(f"Number of packages placed: {400-len(not_placed)}")
        print(f"Number of ULDs that are priority: {len(priority_ULDs)}")
        print(f"Sum of costs of packages not placed: {sum(pkg.cost for pkg in not_placed) + total_priority_cost}")
        print(f"Sum of volume filled: {sum(pkg.get_volume() for pkg in placed)}")
        # Percentage volume not filled
        print(f"Percentage volume filled: {sum(pkg.get_volume() for pkg in placed) / sum(uld.get_volume() for uld in self.ULDs) * 100}%")
        # Percentage of non-priority packages placed
        print(f"Percentage of non-priority packages placed: {(len(placed)-len(priority_pkgs_placed))/(400 - len(priority_pkgs)) * 100}%")
        print()


def cost_function(
    env: Environment,
    priority_check: bool = True,
    collision_check: bool = True,
    weight_limit_check: bool = True,
) -> float:
    cost: int = 0

    if collision_check:
        for uld in env.ULDs:
            events = []
            for pkg in uld.packages:
                events.append({"type": "start", "x": pkg.coords[0][0], "pkg": pkg})
                events.append({"type": "end", "x": pkg.coords[1][0], "pkg": pkg})

            events.sort(key=lambda e: (e["x"], e["type"] == "end"))

            active = []

            for event in events:
                current_pkg = event["pkg"]
                current_y_min, current_y_max = (
                    current_pkg.coords[0][1],
                    current_pkg.coords[1][1],
                )
                current_z_min, current_z_max = (
                    current_pkg.coords[0][2],
                    current_pkg.coords[1][2],
                )
                if event["type"] == "start":
                    for active_pkg in active:
                        active_y_min, active_y_max = (
                            active_pkg.coords[0][1],
                            active_pkg.coords[1][1],
                        )
                        active_z_min, active_z_max = (
                            active_pkg.coords[0][2],
                            active_pkg.coords[1][2],
                        )
                        if not (
                            current_y_max <= active_y_min
                            or current_y_min >= active_y_max
                            or current_z_max <= active_z_min
                            or current_z_min >= active_z_max
                        ):
                            print(
                                f"Collision detected between {current_pkg.id} and {active_pkg.id}"
                            )
                            return float("inf")
                    active.append(current_pkg)
                elif event["type"] == "end":
                    active.remove(current_pkg)

    for uld in env.ULDs:
        if weight_limit_check and uld.weight > uld.weight_limit:
            print("ULD weight limit exceeded")
            return float("inf")
        if uld.has_priority:
            cost += env.K

    for pkg in env.packages:
        if pkg.uld == 0:
            if pkg.is_priority:
                if priority_check:
                    print("Priority package not placed")
                    return float("inf")
            else:
                cost += pkg.cost

    return cost


K = parser.get_K()
uld_list = parser.get_uld_list()
pkg_list = parser.get_pkg_list()

env = Environment(K, uld_list, pkg_list)
env.pack()
# env.plot()
env.summary()

print(cost_function(env, collision_check=False))