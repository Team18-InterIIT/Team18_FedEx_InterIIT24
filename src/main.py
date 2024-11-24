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
        self.cost: int | str = "-" if pkg_row[6] == "-" else int(pkg_row[6])

        self.uld: int = 0
        self.coords: tuple[tuple] = ((-1, -1, -1), (-1, -1, -1))


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
