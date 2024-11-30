import os
import time

import matplotlib.pyplot as plt
import pybullet as p
import pybullet_data
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from sortedcontainers import SortedList
import numpy as np
import streamlit as st

from entity import ULD, Package, Point
from geometry_helpers import is_point_in_convex_hull, rectangle_intersection

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
    stability_id = {1: "Stable", 0: "Not Placed", -1: "Unstable"}

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

    def find_collision(self, uld: ULD, corners_to_check: tuple[Point, Point]):
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
            return -1

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
                return existing_pkg
        return None
    
    def check_collision(self, uld: ULD, corners_to_check: tuple[Point, Point]) -> bool:
        collision_status = self.find_collision(uld, corners_to_check)
        if collision_status is not None:
            return True
        return False

    def check_weight_limit(self, uld: ULD, pkg_weight: int) -> bool:
        """
        Check if the package with the given weight will exceed the weight limit of the ULD

        Returns **True if weight limit is exceeded, False otherwise**
        """
        return uld.weight + pkg_weight > uld.weight_limit

    def apply_gravity(
        self, uld_id: int, corners: tuple[Point, Point], gravity=(0, 0, -1)
    ):
        """
        Apply gravity to the package in the ULD

        Returns the new coordinates of the package, by taking all bottom corners and moving them by gravity
        """
        uld = self.ULDs[uld_id]
        x1_min, y1_min, z1_min = corners[0].x, corners[0].y, corners[0].z
        x1_max, y1_max = corners[1].x, corners[1].y
        height_drop = z1_min

        for pkg in uld.packages:
            if z1_min < pkg.corners[1].z:
                continue

            x0_min, y0_min, x0_max, y0_max, top_surface_height = (
                pkg.corners[0].x,
                pkg.corners[0].y,
                pkg.corners[1].x,
                pkg.corners[1].y,
                pkg.corners[1].z,
            )

            if (min(x1_max, x0_max) - max(x1_min, x0_min)) * (
                min(y1_max, y0_max) - max(y1_min, y0_min)
            ) > 0:
                height_drop = min(height_drop, z1_min - top_surface_height)
                if height_drop == 0:
                    return corners, 0

        return (
            (
                Point(corners[0].x, corners[0].y, corners[0].z - height_drop),
                Point(corners[1].x, corners[1].y, corners[1].z - height_drop),
            ),
            height_drop,
        )

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
        gravity: bool = False,
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

        if stability_check:
            dummy = pkg.copy()
            dummy.corners = corners
            dummy.uld_id = uld.id

            all_corners = dummy.get_corners()
            pkg_id = dummy.id - 1
            if self.check_stability(pkg_id, all_corners) in (-1, 0):
                return False

        if weight_limit_check and self.check_weight_limit(uld, pkg.weight):
            return False

        if not simulate:
            self.pkg_addition_order.append(pkg.id)
            pkg.uld_id = uld.id
            pkg.corners = corners
            if pkg not in self.packages: # For express packages
                self.packages.append(pkg)
            uld.packages.append(pkg)
            uld.weight += pkg.weight
            uld.has_priority = uld.has_priority or pkg.is_priority

        return True
    
    def remove_package(self, pkg: Package, uld: ULD):
        """
        Remove the package from the ULD and update the ULD's weight.

        Parameters:
        pkg (Package): The package to be removed.
        uld (ULD): The ULD from which the package is to be removed.
        """
        self.pkg_addition_order.remove(pkg.id)
        uld.packages.remove(pkg)
        uld.weight -= pkg.weight
        uld.has_priority = any(pkg.is_priority for pkg in uld.packages)
        self.packages.remove(pkg)

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
                            print(
                                f"Collision detected between {pkg1.id} and {pkg2.id} in ULD {uld.id}"
                            )
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

    def sort_by_z(coord):
        return coord[0].z

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
                if self.stable[pkg.id - 1] == -1:
                    if pkg.is_priority:
                        color = "purple"
                    else:
                        color = "orange"

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
        gs = fig.add_gridspec(rows + 1, cols, height_ratios=[*[1] * rows, 0.1])

        for i, uld in enumerate(self.ULDs):
            ax = fig.add_subplot(gs[i], projection="3d")
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
                if self.stable[pkg.id - 1] == -1:
                    if pkg.is_priority:
                        color = "purple"
                    else:
                        color = "orange"

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
    

    def animate_st(self, repeat=False, stepped=True):
        """
        Animate the process of adding packages to the ULDs.

        Parameters:
        repeat (bool): If True, the animation will loop after reaching the last frame.
        stepped (bool): If True, the animation will be drawn step-by-step.
        """
        
        # Create a figure for animation
        fig = plt.figure(figsize=(15, 10))
        num_ULDs = len(self.ULDs)
        rows = 2
        cols = (num_ULDs + 1) // 2
        axes = []
        gs = fig.add_gridspec(rows + 1, cols, height_ratios=[*[1] * rows, 0.1])

        # Create subplots for each ULD
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
            """
            Update function to redraw the animation frame.
            """
            for ax, uld in zip(axes, self.ULDs):
                ax.cla()  # Clear previous plot
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
                if self.stable[pkg.id - 1] == -1:
                    if pkg.is_priority:
                        color = "purple"
                    else:
                        color = "orange"

                ax.add_collection3d(
                    Poly3DCollection(
                        verts,
                        facecolors=color,
                        linewidths=1,
                        edgecolors="r",
                        alpha=0.2,
                    )
                )

            plt.draw()

        # Streamlit session state for tracking the current frame
        if 'current_frame' not in st.session_state:
            st.session_state.current_frame = 0  # Initialize current frame if it doesn't exist

        # Streamlit buttons to control previous and next frame
        prev_button = st.button("Previous")
        next_button = st.button("Next")

        # Button logic for frame navigation
        if prev_button and st.session_state.current_frame > 0:
            st.session_state.current_frame -= 1

        if next_button and st.session_state.current_frame < len(self.pkg_addition_order) - 1:
            st.session_state.current_frame += 1

        # Update the plot with the current frame
        update(st.session_state.current_frame)

        # Return the figure to be displayed in Streamlit
        plt.tight_layout()
        return fig

    def reset_simulation(self, uld_ids):
        p.resetSimulation()
        p.setAdditionalSearchPath(
            pybullet_data.getDataPath()
        )  # Adds search path for PyBullet data (like URDFs)
        p.setGravity(0, 0, -9.8)  # Set gravity

        package_list = []  # List to store package IDs
        gap = 20  # Gap between each ULD

        for index, uld_id in enumerate(uld_ids):
            uld = self.ULDs[uld_id]
            x_offset = index * (cm_to_m(uld.dim.l) + cm_to_m(gap))

            # Add bottom wall (floor) for the ULD
            floor_thickness = 0.1

            # Bottom wall
            p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        cm_to_m(uld.dim.l) / 2,
                        cm_to_m(uld.dim.w) / 2,
                        floor_thickness / 2,
                    ],
                ),
                basePosition=[
                    x_offset + cm_to_m(uld.dim.l) / 2,
                    cm_to_m(uld.dim.w) / 2,
                    -floor_thickness / 2,
                ],
            )

            # Add transparent walls around the ULD
            wall_thickness = 0.1
            wall_height = cm_to_m(uld.dim.h)

            # Left wall
            left_wall_visual = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[
                    wall_thickness / 2,
                    cm_to_m(uld.dim.w) / 2,
                    wall_height / 2,
                ],
                rgbaColor=[1, 1, 1, 0],  # Fully transparent color
            )
            p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        wall_thickness / 2,
                        cm_to_m(uld.dim.w) / 2,
                        wall_height / 2,
                    ],
                ),
                baseVisualShapeIndex=left_wall_visual,
                basePosition=[
                    x_offset - wall_thickness / 2,
                    cm_to_m(uld.dim.w) / 2,
                    wall_height / 2,
                ],
            )

            # Right wall
            right_wall_visual = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[
                    wall_thickness / 2,
                    cm_to_m(uld.dim.w) / 2,
                    wall_height / 2,
                ],
                rgbaColor=[1, 1, 1, 0],  # Fully transparent color
            )
            p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        wall_thickness / 2,
                        cm_to_m(uld.dim.w) / 2,
                        wall_height / 2,
                    ],
                ),
                baseVisualShapeIndex=right_wall_visual,
                basePosition=[
                    x_offset + cm_to_m(uld.dim.l) + wall_thickness / 2,
                    cm_to_m(uld.dim.w) / 2,
                    wall_height / 2,
                ],
            )

            # Front wall
            front_wall_visual = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[
                    cm_to_m(uld.dim.l) / 2,
                    wall_thickness / 2,
                    wall_height / 2,
                ],
                rgbaColor=[1, 1, 1, 0],  # Fully transparent color
            )
            p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        cm_to_m(uld.dim.l) / 2,
                        wall_thickness / 2,
                        wall_height / 2,
                    ],
                ),
                baseVisualShapeIndex=front_wall_visual,
                basePosition=[
                    x_offset + cm_to_m(uld.dim.l) / 2,
                    -wall_thickness / 2,
                    wall_height / 2,
                ],
            )

            # Back wall
            back_wall_visual = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[
                    cm_to_m(uld.dim.l) / 2,
                    wall_thickness / 2,
                    wall_height / 2,
                ],
                rgbaColor=[1, 1, 1, 0],  # Fully transparent color
            )
            p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        cm_to_m(uld.dim.l) / 2,
                        wall_thickness / 2,
                        wall_height / 2,
                    ],
                ),
                baseVisualShapeIndex=back_wall_visual,
                basePosition=[
                    x_offset + cm_to_m(uld.dim.l) / 2,
                    cm_to_m(uld.dim.w) + wall_thickness / 2,
                    wall_height / 2,
                ],
            )

            # Iterate over the packages in the ULD
            for pkg in uld.packages:
                # Create the collision shape for the package (a box)
                package_shape = p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        cm_to_m(pkg.corners[1].x - pkg.corners[0].x) / 2,
                        cm_to_m(pkg.corners[1].y - pkg.corners[0].y) / 2,
                        cm_to_m(pkg.corners[1].z - pkg.corners[0].z) / 2,
                    ],
                )

                color = (
                    [1, 0, 0, 0.7] if self.stable[pkg.id - 1] == -1 else [0, 1, 0, 0.7]
                )

                # Create the visual shape for the package with a specific color
                package_visual = p.createVisualShape(
                    p.GEOM_BOX,
                    halfExtents=[
                        cm_to_m(pkg.corners[1].x - pkg.corners[0].x) / 2,
                        cm_to_m(pkg.corners[1].y - pkg.corners[0].y) / 2,
                        cm_to_m(pkg.corners[1].z - pkg.corners[0].z) / 2,
                    ],
                    rgbaColor=color,  # Set the color for the package
                )

                # Calculate the global coordinates of the package based on the corners (assuming pkg.corners is a list of two points)
                global_coords = [
                    x_offset
                    + cm_to_m(pkg.corners[0].x + pkg.corners[1].x)
                    / 2,  # x-coordinate of the center
                    cm_to_m(pkg.corners[0].y + pkg.corners[1].y)
                    / 2,  # y-coordinate of the center
                    cm_to_m(pkg.corners[0].z + pkg.corners[1].z)
                    / 2,  # z-coordinate of the center
                ]

                # Create the package body in the simulation with the calculated global position
                package_id = p.createMultiBody(
                    baseMass=pkg.weight,
                    baseCollisionShapeIndex=package_shape,
                    baseVisualShapeIndex=package_visual,
                    basePosition=global_coords,
                )
                package_list.append(package_id)

    def simulate(self, uld_ids=None):
        if uld_ids is None:
            uld_ids = list(range(len(self.ULDs)))
        # Connect to the physics engine in GUI mode
        p.connect(p.GUI)
        self.reset_simulation(uld_ids)

        print("Press 'c' to start the simulation...")
        while True:
            keys = p.getKeyboardEvents()
            if ord("c") in keys and keys[ord("c")] & p.KEY_WAS_TRIGGERED:
                break
            time.sleep(0.1)

        # Start the simulation
        while True:
            keys = p.getKeyboardEvents()
            if ord("x") in keys and keys[ord("x")] & p.KEY_WAS_TRIGGERED:
                self.reset_simulation(uld_ids)
                print("Simulation reset. Press 'c' to start again.")
                while True:
                    keys = p.getKeyboardEvents()
                    if ord("c") in keys and keys[ord("c")] & p.KEY_WAS_TRIGGERED:
                        break
                    time.sleep(0.1)
            p.stepSimulation()
            time.sleep(1 / 240)

        p.disconnect()

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
