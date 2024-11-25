import itertools
import heapq

from algorithm_interface import PackingAlgorithm
from entity import ULD, Package, Point
from environment import Environment


class ThreeDBP_Pivoting(PackingAlgorithm):
    def solve(self, env: Environment):
        """
        https://github.com/enzoruiz/3dbinpacking/blob/master/erick_dube_507-034.pdf
        """

        def pivot_package(pkg: Package, uld: ULD, pivot: Point, signs) -> bool:
            for l_inc, w_inc, h_inc in itertools.permutations(
                [pkg.dim.l, pkg.dim.w, pkg.dim.h]
            ):
                l_inc = signs[0] * l_inc
                w_inc = signs[1] * w_inc
                h_inc = signs[2] * h_inc
                corners = (
                    Point(
                        *map(
                            min,
                            zip(
                                (pivot.x, pivot.y, pivot.z),
                                (pivot.x + l_inc, pivot.y + w_inc, pivot.z + h_inc),
                            ),
                        )
                    ),
                    Point(
                        *map(
                            max,
                            zip(
                                (pivot.x, pivot.y, pivot.z),
                                (pivot.x + l_inc, pivot.y + w_inc, pivot.z + h_inc),
                            ),
                        )
                    ),
                )
                return env.add_package(pkg, uld, corners=corners)

        def generate_corners(existing_pkg):
            x, y, z = (
                existing_pkg.corners[0].x,
                existing_pkg.corners[0].y,
                existing_pkg.corners[0].z,
            )
            l, w, h = existing_pkg.dim.l, existing_pkg.dim.w, existing_pkg.dim.h
            return [
                (Point(x + l, y, z), (1, 1, 1)),
                (Point(x, y + w, z), (1, 1, 1)),
                (Point(x, y, z + h), (1, 1, 1)),
                (Point(x + l, y, z), (-1, -1, 1)),
                (Point(x, y + w, z), (-1, -1, 1)),
            ]

        def pack_to_ULD(pkg: Package, uld: ULD) -> bool:
            """
            Pack the package to the ULD
            """
            if pkg.uld_id != 0:
                return False

            if not uld.packages:
                return pivot_package(pkg, uld, Point(0, 0, 0), (1, 1, 1))

            for existing_pkg in uld.packages:
                for pivot, signs in generate_corners(existing_pkg):
                    if pivot_package(pkg, uld, pivot, signs):
                        return True

            return False

        sorted_ULDs = sorted(env.ULDs, key=lambda uld: uld.volume(), reverse=True)
        sorted_pkgs = sorted(
            env.packages, key=lambda pkg: pkg.cost / pkg.volume(), reverse=True
        )
  
        for uld in sorted_ULDs:
            for pkg in sorted_pkgs:
                pack_to_ULD(pkg, uld)

        for uld in sorted_ULDs:
            for pkg in sorted_pkgs:
                pack_to_ULD(pkg, uld)
