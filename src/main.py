class dim:
    def __init__(self, length: int, width: int, height: int):
        self.l: int = length
        self.w: int = width
        self.h: int = height


class Package:
    # attributes
    def __init__(self, pkg_row: list[str], uld: int, coords: tuple[tuple]):
        # id, length, width, hegiht, wt, type, cost (strings)
        self.id: str = pkg_row[0]
        self.dim: dim = dim(int(pkg_row[1]), int(pkg_row[2]), int(pkg_row[3]))
        self.weight: int = int(pkg_row[4])
        self.type: bool = pkg_row[5] == "Priority"
        self.cost: int = int(pkg_row[6])


class ULD:
    def _init_(self, uld_list):
        self.priority = False
        self.weight = 0
        self.dim = dim(self, int(uld_list[1]), int(uld_list[2]), int(uld_list[3]))

        self.identifier: str = uld_list[0]
        self.weight_limit: int = int(uld_list[4])


class Environment:
    def __init__(self, K, uld_list, pkg_list):
        self.packages = list()
        default_pos = ((-1, -1, -1), (-1, -1, -1))
        for pkg_data_row in pkg_list:
            self.packages.append(Package(pkg_data_row, 0, default_pos))

        self.ULDs = [None]

        for uld_data_row in uld_list:
            self.ULDs.append(ULD(uld_data_row))
