import os

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from matplotlib.widgets import Button

from entity import ULD, Package, Point

from geometry_helpers import rectangle_intersection, is_point_in_convex_hull

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

    def new(self):
        return Environment(self.K, [], [])

    def reset(self):
        for uld in self.ULDs:
            uld.reset()

        for pkg in self.packages:
            pkg.reset()

        self.pkg_addition_order = []

    def copy_from(self, other: "Environment"):
        self.K = other.K
        self.packages = [pkg.copy() for pkg in other.packages]
        self.ULDs = [uld.copy() for uld in other.ULDs]
        self.pkg_addition_order = other.pkg_addition_order.copy()

    def copy(self):
        new_env = self.new()
        new_env.copy_from(self)
        return new_env

    def check_collision(self, uld: ULD, corners_to_check: tuple[Point, Point]) -> bool:
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
            ) or (
                corners_to_check[0].x == existing_pkg.corners[1].x
                and corners_to_check[1].x == existing_pkg.corners[0].x
                and corners_to_check[0].y == existing_pkg.corners[1].y
                and corners_to_check[1].y == existing_pkg.corners[0].y
                and corners_to_check[0].z == existing_pkg.corners[1].z
                and corners_to_check[1].z == existing_pkg.corners[0].z
            ):
                return True

        return False

    def check_weight_limit(self, uld: ULD, pkg_weight: int) -> bool:
        """
        Check if the package with the given weight will exceed the weight limit of the ULD

        Returns **True if weight limit is exceeded, False otherwise**
        """
        return uld.weight + pkg_weight > uld.weight_limit

    def add_package(
        self,
        pkg: Package | int,
        uld: ULD | int,
        corners: tuple[Point, Point],
        simulate: bool = False,
        collision_check: bool = True,
        weight_limit_check: bool = True,
        floating_check: bool = True,
        stability_check: bool = True,
        fragility_check: bool = True,
    ) -> bool:
        """
        Add a package to the ULD at the given coordinates,
        taking into account various constraints

        Returns **True if the package is successfully added, False otherwise**
        """
        if isinstance(pkg, int):
            pkg = self.packages[pkg - 1]

        if isinstance(uld, int):
            uld = self.ULDs[uld - 1]

        if collision_check and self.check_collision(uld, corners):
            return False

        if weight_limit_check and self.check_weight_limit(uld, pkg.weight):
            return False

        if not simulate:
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
                for pkg1_id in range(len(uld.packages)):
                    pkg1 = uld.packages[pkg1_id]
                    for pkg2_id in range(pkg1_id + 1, len(uld.packages)):
                        pkg2 = uld.packages[pkg2_id]
                        if (
                            pkg1.corners[0].x < pkg2.corners[1].x
                            and pkg1.corners[1].x > pkg2.corners[0].x
                            and pkg1.corners[0].y < pkg2.corners[1].y
                            and pkg1.corners[1].y > pkg2.corners[0].y
                            and pkg1.corners[0].z < pkg2.corners[1].z
                            and pkg1.corners[1].z > pkg2.corners[0].z
                        ):
                            print(f"Collision detected between {pkg1.id} and {pkg2.id}")
                            return float("inf"), float("inf")

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

                color = "green" if not pkg.is_priority else "cyan"

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
        self.check_stability()
        delay_cost, priority_cost = self.cost()

        packages = set(pkg for pkg in self.packages)
        placed = set(pkg for pkg in self.packages if pkg.uld_id != 0)
        not_placed = packages - placed

        priority_ULDs = set(uld for uld in self.ULDs if uld.has_priority)
        priority_pkgs = set(pkg for pkg in self.packages if pkg.is_priority)
        priority_pkgs_placed = priority_pkgs & placed

        print(
            f"Number of packages placed: {len(placed)}\nNumber of packages not placed: {len(not_placed)}"
            f"\nNumber of stable packages: {len([pkg for pkg in self.packages if self.stable[pkg.id] == 'Stable'])}"
            f"\nNumber of unstable packages: {len([pkg for pkg in self.packages if self.stable[pkg.id] == 'Unstable'])}"
            f"\nNumber of ULDs that are priority: {len(priority_ULDs)}"
            f"\nPercentage volume filled: {round(sum(pkg.volume() for pkg in placed) / sum(uld.volume() for uld in self.ULDs) * 100, 3)}%"
            f"\nPercentage of non-priority packages placed: {round((len(placed) - len(priority_pkgs_placed)) / (len(packages) - len(priority_pkgs)) * 100, 3) if len(packages) != len(priority_pkgs) else 100}%"
            f"\nCost ==> Priority: {priority_cost} + Delay: {delay_cost} = {priority_cost + delay_cost}"
        )

    def animate(self, repeat=False, stepped=True):
        """
        Animate the process of adding packages to the ULDs.

        Parameters:
        repeat (bool): If True, the animation will loop after reaching the last frame.
        stepped (bool): If True, the animation will be drawn step-by-step.
        """

        fig = plt.figure(figsize=(15, 10))
        num_ULDs = len(self.ULDs)
        rows = 2
        cols = (num_ULDs + 1) // 2
        axes = []
        gs = fig.add_gridspec(rows + 1, cols, height_ratios=[*[1] * rows, 0.1])

        for i, uld in enumerate(self.ULDs):
            ax = fig.add_subplot(gs[i], projection="3d")
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

                color = "green" if not pkg.is_priority else "cyan"

                ax.add_collection3d(
                    Poly3DCollection(
                        verts,
                        facecolors=color,
                        linewidths=1,
                        edgecolors="r",
                        alpha=0.2,
                    )
                )
            if stepped:
                plt.draw()

        if stepped:
            ax_prev = fig.add_subplot(gs[-1, 0])
            ax_next = fig.add_subplot(gs[-1, -1])
            btn_prev = Button(ax_prev, "Previous")
            btn_next = Button(ax_next, "Next")

            # Current frame tracking
            current_frame = -1

            def next_frame(event):
                nonlocal current_frame
                if current_frame < len(self.pkg_addition_order) - 1:
                    current_frame += 1
                    update(current_frame)
                    print(
                        "Added package",
                        self.pkg_addition_order[current_frame],
                        "which is",
                        self.stable[self.pkg_addition_order[current_frame]],
                    )

            def prev_frame(event):
                nonlocal current_frame
                if current_frame >= 0:
                    current_frame -= 1
                    update(current_frame)
                    print(
                        "Removed package",
                        self.pkg_addition_order[current_frame],
                        "which is",
                        self.stable[self.pkg_addition_order[current_frame]],
                    )

            # Connect buttons to frame navigation
            btn_next.on_clicked(next_frame)
            btn_prev.on_clicked(prev_frame)

        else:
            frames = range(0, len(self.pkg_addition_order))

            _ = FuncAnimation(
                fig,
                update,
                frames=frames,
                repeat=repeat,
            )

        plt.tight_layout()
        plt.show()
        plt.close()

    def write(self, file_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        file_path = os.path.join(project_root, file_path)
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        with open(file_path, "w") as f:
            cost = sum(self.cost())
            if cost != float("inf"):
                cost = int(cost)
            f.write(
                f"{cost},{sum((1 for pkg in self.packages if pkg.uld_id != 0))},{sum((1 for uld in self.ULDs if uld.has_priority))}\n"
            )
            for pkg in self.packages:
                f.write(
                    f"P-{pkg.id},ULD-{pkg.uld_id},{pkg.corners[0].x},{pkg.corners[0].y},{pkg.corners[0].z},{pkg.corners[1].x},{pkg.corners[1].y},{pkg.corners[1].z}\n"
                )

    def read(self, file_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        file_path = os.path.join(project_root, file_path)

        with open(file_path, "r") as f:
            lines = f.readlines()
            for line in lines[1:]:
                pkg_id, uld_id, x1, y1, z1, x2, y2, z2 = line.strip().split(",")
                pkg_id = int(pkg_id.split("-")[1])
                uld_id = int(uld_id.split("-")[1])
                x1, y1, z1, x2, y2, z2 = map(int, (x1, y1, z1, x2, y2, z2))

                pkg = self.packages[pkg_id - 1]
                pkg.uld_id = uld_id
                pkg.corners = (Point(x1, y1, z1), Point(x2, y2, z2))

            for pkg in self.packages:
                if pkg.uld_id == 0:
                    continue
                self.ULDs[pkg.uld_id - 1].packages.append(pkg)

            for uld in self.ULDs:
                uld.has_priority = any(pkg.is_priority for pkg in uld.packages)
                uld.weight = sum(pkg.weight for pkg in uld.packages)

    def check_stability(self):
        """
        First make a dictionary with pk_id as the key and the coordinates
        of the package sorted by z-coordinate as the value

        Whichever boxes are on the ground are already stable and no check needs
        to be performed on them.

        pkg_coords holds the rest of the packages and their coordinates
        """

        # Make a dictionary with pkid as the key and the coords as the value
        stable_coords = []
        unstable_pkgs = {}
        self.stable = {}

        for pkg in self.packages:
            to_insert = sorted(pkg.get_corners(), key=lambda coord: coord.z)
            if to_insert[0].z == 0:
                self.stable[pkg.id] = "Stable"
                stable_coords.append(to_insert[4:])
            elif to_insert[0].z == -1:
                self.stable[pkg.id] = "Not Placed"
            else:
                self.stable[pkg.id] = "Unstable"
                unstable_pkgs[pkg.id] = to_insert

        # Sort unstable packages with respect to z coordinate then x then y
        unstable_pkgs = dict(
            sorted(
                unstable_pkgs.items(),
                key=lambda item: (item[1][0].z, item[1][0].x, item[1][0].y),
            )
        )

        curr_z = 0
        left_z = 0
        right_z = -1

        for pkg_id in unstable_pkgs:
            stable_coords = sorted(
                stable_coords, key=lambda coord: (coord[0].z, coord[0].x, coord[0].y)
            )
            curr_bottom = unstable_pkgs[pkg_id][:4]
            if unstable_pkgs[pkg_id][0].z > curr_z:
                curr_z = unstable_pkgs[pkg_id][0].z
                left_z = right_z + 1
                for i in range(left_z, len(stable_coords)):
                    if stable_coords[i][0].z > curr_z:
                        right_z = i - 1
                        break
                    elif stable_coords[i][0].z < curr_z:
                        left_z = i + 1
                else:
                    right_z = len(stable_coords) - 1

            if left_z > right_z:
                self.stable[pkg_id] = "Unstable"
                continue

            # Dimensions of the package's ULD
            l = self.ULDs[self.packages[pkg_id - 1].uld_id - 1].dim.l
            w = self.ULDs[self.packages[pkg_id - 1].uld_id - 1].dim.w
            h = self.ULDs[self.packages[pkg_id - 1].uld_id - 1].dim.h

            if (
                (unstable_pkgs[pkg_id][0].x == 0 and unstable_pkgs[pkg_id][0].y == 0)
                or (unstable_pkgs[pkg_id][2].x == 0 and unstable_pkgs[pkg_id][2].y == w)
                or (unstable_pkgs[pkg_id][4].x == l and unstable_pkgs[pkg_id][4].y == 0)
                or (unstable_pkgs[pkg_id][6].x == l and unstable_pkgs[pkg_id][6].y == w)
                or unstable_pkgs[pkg_id][7].z == h
            ):
                self.stable[pkg_id] = "Stable"
                stable_coords.append(unstable_pkgs[pkg_id][4:])
                continue

            # Find the range of intersecting intervals in O(log n)
            start_x = right_z + 1

            target_left = curr_bottom[0].x
            target_right = curr_bottom[2].x

            left, right = left_z, right_z

            while left <= right:
                mid = (left + right) // 2

                # Check if current interval intersects
                if max(stable_coords[mid][0].x, target_left) <= min(
                    stable_coords[mid][2].x, target_right
                ):
                    # This interval intersects, remember this index and look left
                    start_x = min(start_x, mid)
                    right = mid - 1
                elif stable_coords[mid][2].x < target_left:
                    # Move right if current interval is completely before target
                    left = mid + 1
                else:
                    # Move left if current interval is completely after target
                    right = mid - 1

            # If no intersecting intervals found, return empty list
            if start_x == right_z + 1:
                self.stable[pkg.id] = "Unstable"
                continue

            # Find the end of intersecting intervals in O(log n)
            end_x = start_x - 1

            left, right = start_x, right_z

            while left <= right:
                mid = (left + right) // 2

                # Check if current interval intersects
                if max(stable_coords[mid][0].x, target_left) <= min(
                    stable_coords[mid][2].x, target_right
                ):
                    # This interval intersects, remember this index and look right
                    end_x = max(end_x, mid)
                    left = mid + 1
                elif stable_coords[mid][0].x > target_right:
                    # Move left if current interval is completely after target
                    right = mid - 1
                else:
                    # Move right if current interval starts before target ends
                    left = mid + 1

            start_y = end_x + 1

            target_left = curr_bottom[0].y
            target_right = curr_bottom[1].y

            left = start_x
            right = end_x

            while left <= right:
                mid = (left + right) // 2

                # Check if current interval intersects
                if max(stable_coords[mid][0].y, target_left) <= min(
                    stable_coords[mid][1].y, target_right
                ):
                    # This interval intersects, remember this index and look left
                    start_y = min(start_y, mid)
                    right = mid - 1
                elif stable_coords[mid][1].y < target_left:
                    # Move right if current interval is completely before target
                    left = mid + 1
                else:
                    # Move left if current interval is completely after target
                    right = mid - 1

            # If no intersecting intervals found, return empty list
            if start_y == end_x + 1:
                self.stable[pkg.id] = "Unstable"
                continue

            # Find the end of intersecting intervals in O(log n)
            end_y = start_y - 1

            left, right = start_y, end_x

            while left <= right:
                mid = (left + right) // 2

                # Check if current interval intersects
                if max(stable_coords[mid][0].y, target_left) <= min(
                    stable_coords[mid][1].y, target_right
                ):
                    # This interval intersects, remember this index and look right
                    end_y = max(end_y, mid)
                    left = mid + 1
                elif stable_coords[mid][0].y > target_right:
                    # Move left if current interval is completely after target
                    right = mid - 1
                else:
                    # Move right if current interval starts before target ends
                    left = mid + 1

            result_start = start_y
            result_end = end_y

            # For each set of coordinates in the range, make an intersection

            hull_points = []

            for i in range(result_start, result_end + 1):
                hull_points.extend(
                    rectangle_intersection(stable_coords[i], curr_bottom)
                )

            # Check if the mid point of curr_bottom is inside the hull
            mid_point = (curr_bottom[0].x + curr_bottom[2].x) / 2, (
                curr_bottom[0].y + curr_bottom[1].y
            ) / 2
            if is_point_in_convex_hull(hull_points, mid_point):
                self.stable[pkg_id] = "Stable"
                stable_coords.append(unstable_pkgs[pkg_id][4:])
            else:
                self.stable[pkg_id] = "Unstable"
