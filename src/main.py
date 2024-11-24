import parser

DEFAULT_NUMBER_OF_DECIMALS = 3

START_POSITION = [0, 0, 0]

axes_id = {'length':0, 'breadth':1, 'height':2}

class dim:
    def __init__(self, length: int, width: int, height: int):
        self.l: int = length
        self.w: int = width
        self.h: int = height


class Package:
    def __init__(self, pkg_row: list[str]):
        # id, length, width, hegiht, wt, type, cost (strings)
        self.id: str = pkg_row[0]
        self.dim: dim = dim(int(pkg_row[1]), int(pkg_row[2]), int(pkg_row[3]))
        self.weight: int = int(pkg_row[4])
        self.is_priority: bool = pkg_row[5] == "Priority"
        self.cost: float = float('inf') if self.is_priority else float(pkg_row[6])

        self.uld: int = 0
        self.coords: tuple[tuple] = ((-1, -1, -1), (-1, -1, -1))

    
    def get_volume(self):
        return self.width * self.height * self.depth, self.number_of_decimals


class ULD:
    def __init__(self, uld_row: list[str]):
        self.id: str = uld_row[0]
        self.dim: dim = dim(int(uld_row[1]), int(uld_row[2]), int(uld_row[3]))
        self.weight_limit: int = int(uld_row[4])

        self.has_priority: bool = False
        self.weight: int = 0
        self.packages: list[Package] = list()


class Environment:
    def __init__(self, K, uld_list, pkg_list):
        self.K = K

        self.packages: list[Package] = list()
        for pkg_data_row in pkg_list:
            self.packages.append(Package(pkg_data_row))

        self.ULDs: list[ULD] = [None]
        for uld_data_row in uld_list:
            self.ULDs.append(ULD(uld_data_row))

    def check_collision(self, uld_id: int, coords: tuple[tuple]):
        for pkg in self.ULDs[uld_id].packages:
            if (
                coords[0][0] < pkg.coords[1][0]
                and coords[1][0] > pkg.coords[0][0]
                and coords[0][1] < pkg.coords[1][1]
                and coords[1][1] > pkg.coords[0][1]
                and coords[0][2] < pkg.coords[1][2]
                and coords[1][2] > pkg.coords[0][2]
            ):
                return True

        return False

    def check_weight_limit(self, uld_id: int, pkg_weight: int):
        return self.ULDs[uld_id].weight + pkg_weight > self.ULDs[uld_id].weight_limit

    def add_package(
        self,
        pkg_id: id,
        uld_id: id,
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
            uld_id, self.packages[pkg_id].weight
        ):
            return False

        pkg = self.packages[pkg_id]
        uld = self.ULDs[uld_id]

        pkg.uld = uld_id
        pkg.coords = coords

        uld.packages.append(pkg)
        uld.weight += pkg.weight
        uld.has_priority = uld.has_priority or pkg.is_priority


def cost_function(
    env: Environment,
    priority_check: bool = True,
    collision_check: bool = True,
    weight_limit_check: bool = True,
) -> float:
    cost: int = 0

    if collision_check:
        for uld in env.ULDs:
            if uld is None:
                continue

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
        if uld is None:
            continue
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

