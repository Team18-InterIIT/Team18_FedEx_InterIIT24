import itertools

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment


class ThreeDBP_Pivoting(PackingAlgorithm):
    def solve(self, env):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        """

        def pivot_package(pkg: Package, uld: ULD, pivot: Point) -> bool:
            for l_inc, b_inc, h_inc in itertools.permutations(
                [pkg.dim.l, pkg.dim.w, pkg.dim.h]
            ):
                if env.add_package(
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

        def pack_to_ULD(pkg: Package, uld: ULD) -> bool:
            """
            Pack the package to the ULD
            """
            if not uld.packages:
                return pivot_package(pkg, uld, Point(0, 0, 0))

            for axis in range(0, 3):
                for existing_pkg in uld.packages:
                    pivot = Point(0, 0, 0)
                    l, w, h = existing_pkg.dim.l, existing_pkg.dim.w, existing_pkg.dim.h
                    if axis == Environment.axes_id["length"]:
                        pivot = Point(
                            existing_pkg.corners[0].x + l,
                            existing_pkg.corners[0].y,
                            existing_pkg.corners[0].z,
                        )
                    elif axis == Environment.axes_id["width"]:
                        pivot = Point(
                            existing_pkg.corners[0].x,
                            existing_pkg.corners[0].y + w,
                            existing_pkg.corners[0].z,
                        )
                    elif axis == Environment.axes_id["height"]:
                        pivot = Point(
                            existing_pkg.corners[0].x,
                            existing_pkg.corners[0].y,
                            existing_pkg.corners[0].z + h,
                        )

                    if pivot_package(pkg, uld, pivot):
                        return True

            return False

        sorted_ULDs = sorted(env.ULDs, key=lambda uld: uld.volume(), reverse=True)
        sorted_pkgs = sorted(
            env.packages,
            key=lambda pkg: pkg.cost**1.5 / pkg.volume(),
            reverse=True,
        )
        for uld in sorted_ULDs:
            for pkg in sorted_pkgs:
                if pkg.uld_id == 0:
                    pack_to_ULD(pkg, uld)

        for pkg in env.packages:
            if pkg.uld_id == 0:
                for uld in env.ULDs:
                    pack_to_ULD(pkg, uld)
