import collections

import hyperpack as hp

from entity import ULD, Dim, Package, Point
from environment import Environment


class Rect:
    """
    Represents a package in a layer

    Attributes
    ----------
    id: int
        The ID of the package
    dim: Dim
        The dimensions of the package
    weight: int
        The weight of the package
    is_priority: bool
        Whether the package is a priority package
    cost: float
        The cost of the package
    is_packed: bool
        Whether the package is packed in the layer
    """

    def __init__(
        self,
        pkg: Package,
        x: int,
        y: int,
        l: int,
        w: int,
        h: int,
        is_packed: bool = False,
    ):
        self.id: int = pkg.id
        self.dim: Dim = Dim(l, w, h)
        self.weight: int = pkg.weight
        self.is_priority: bool = pkg.is_priority
        self.cost: float = pkg.cost

        self.is_packed: bool = is_packed

    def __repr__(self) -> str:
        return f"Rect ID: {self.id}, Dim: {self.dim}, Weight: {self.weight}, Cost: {self.cost}"

    @property
    def area(self) -> int:
        return self.dim.l * self.dim.w


class Layer:
    """
    Represents a layer of packages in a ULD

    Attributes
    ----------
    rects: list[Rect]
        List of packages in the layer
    uld: ULD
        The ULD in which the packages are packed
    dim: Dim
        The dimensions of the layer

    Functions
    ---------
    new() -> Layer:
        Returns a new instance of Layer
    area_covered() -> int:
        Returns the area covered by the packages in the layer
    packing_eff() -> float:
        Returns the packing efficiency of the layer
    area() -> float:
        Returns the area of the base of the layer
    cost() -> float:
        Returns the cost of the layer
    weight() -> int:
        Returns the weight of the layer
    height_ratio() -> float:
        Returns the height ratio of the layer
    weight_ratio() -> float:
        Returns the weight ratio of the layer
    cost_density() -> float:
        Returns the cost density of the layer
    add_rect(pkg: Rect):
        Adds a package to the layer
    """

    def __init__(
        self,
        pkgs: list[Rect],
        uld: ULD,
        height: int,
    ):
        self.rects: list[Rect] = pkgs
        self.uld: ULD = uld
        self.dim: Dim = Dim(uld.dim.l, uld.dim.w, height)

    def new() -> "Layer":
        return Layer([], ULD.new(), 0, 0, 0)

    @property
    def area_covered(self) -> int:
        return sum([rect.area for rect in self.rects])

    @property
    def packing_eff(self) -> float:
        return self.area_covered / self.area

    @property
    def area(self) -> float:
        return self.dim.l * self.dim.w

    @property
    def cost(self) -> float:
        return sum([rect.cost if not rect.is_priority else 1e9 for rect in self.rects])

    @property
    def weight(self) -> int:
        return sum([rect.weight for rect in self.rects])

    def height_ratio(self) -> float:
        return self.dim.h / self.uld.dim.h

    def weight_ratio(self) -> float:
        return self.weight / self.uld.weight_limit

    def cost_density(self) -> float:
        return self.cost / self.uld.volume()

    def add_rect(self, pkg: Rect):
        self.rects.append(pkg)

    def __repr__(self) -> str:
        return f"ULD: {self.uld.id}, Height: {self.dim.h}, Weight: {self.weight}, Cost: {self.cost}, Packing Efficiency: {self.packing_eff}"


def get_dim_freq(packages, margin):
    """
    Calculate the frequency of dimensions in the given packages.

    Parameters
    ----------
    packages (list): A list of packages, each with dimensions.
    margin (int): A parameter to adjust the dimension frequency calculation.

    Returns
    -------
    list: A sorted list of tuples containing dimensions and their frequencies.
    """
    dimension_frequency = collections.Counter()

    for pkg in packages:
        dims = set([pkg.dim.l, pkg.dim.w, pkg.dim.h])
        for j, dim in enumerate(dims):
            for i in range(margin + 1):
                if pkg.can_be_rotated or j == 2:
                    dimension_frequency[dim + i] += 1
    dimension_frequency = sorted(
        dimension_frequency.items(), key=lambda x: x[1], reverse=True
    )
    return dimension_frequency


def selectrects(height: int, packages: list[Package]) -> list[Rect]:
    """
    Selects packages with a given height from the list of packages
    """
    selectedrects = []
    for pkg in packages:
        if pkg.id not in selectedrects:
            if height in pkg.dim:
                l, w, h = pkg.dim
                if pkg.can_be_rotated and l == height:
                    selectedrects.append(Rect(pkg, 0, 0, w, h, height, is_packed=False))
                elif pkg.can_be_rotated and w == height:
                    selectedrects.append(Rect(pkg, 0, 0, l, h, height, is_packed=False))
                elif h == height:
                    selectedrects.append(Rect(pkg, 0, 0, l, w, height, is_packed=False))
    return selectedrects


def bp2d(layer: Layer, selectedrects: list[Rect]):
    """
    2D Bin Packing Algorithm
    """
    uld = layer.uld
    container = {f"ULD{uld.id}": {"L": uld.dim.w, "W": uld.dim.l}}
    items = {str(rect.id): {"w": rect.dim.l, "l": rect.dim.w} for rect in selectedrects}

    problem = hp.HyperPack(containers=container, items=items)
    problem.local_search()

    for _, items in problem.solution.items():
        for rect in selectedrects:
            if str(rect.id) not in items:
                continue
            x, y, l, w = items[str(rect.id)]
            rect.x = x
            rect.y = y
            rect.dim.l = l
            rect.dim.w = w
            layer.add_rect(rect)
            rect.is_packed = True


def remove_rect(packages: list[Package], rect: Rect):
    """
    Remove a package from the list of packages
    """
    for i, pkg in enumerate(packages):
        if pkg.id == rect.id:
            packages.pop(i)
            break


def _make_layers(
    packages: list[Package],
    uld: ULD,
    rejection_threshold: int,
    weight_ratio_threshold: int,
    margin: int,
) -> list[Layer]:
    """
    Make layers of packages in a ULD
    """
    layers = []
    if len(packages) == 0:
        return layers
    dimension_frequency = get_dim_freq(packages, margin)
    length = uld.dim.l
    width = uld.dim.w

    dim_idx = 0
    previous_selectedrects = []
    while dim_idx < len(dimension_frequency):
        dim = dimension_frequency[dim_idx]

        selectedrects = selectrects(int(dim[0]), packages)
        if len(selectedrects) == 0:
            dim_idx += 1
            continue

        if len(selectedrects) == len(previous_selectedrects):
            if all(
                rect1.id == rect2.id
                for rect1, rect2 in zip(selectedrects, previous_selectedrects)
            ):
                dim_idx += 1
                continue

        area = sum([rect.dim.l * rect.dim.w for rect in selectedrects])

        height_ratio = int(dim[0]) / uld.dim.h

        if area >= length * width * rejection_threshold:
            layer = Layer([], uld, int(dim[0]))
            bp2d(layer, selectedrects)
            if len(layer.rects) == 0:
                dim_idx += 1
                continue

            layer.height_ratio = height_ratio
            layer.weight_ratio = layer.weight / uld.weight_limit

            if (
                layer.packing_eff >= rejection_threshold
                and layer.weight_ratio <= weight_ratio_threshold * layer.height_ratio
            ):
                layers.append(layer)

        previous_selectedrects = selectedrects

    return layers


def make_layers(
    packages: list[Package],
    uld: ULD,
    rejection_threshold=0.9,
    weight_ratio_threshold=0.3,
    margin=0,
) -> list[Layer]:
    """
    Make layers of packages in a ULD with different tolerances
    """
    all_layers = []
    layers = _make_layers(
        packages,
        uld,
        rejection_threshold,
        weight_ratio_threshold,
        margin,
    )

    all_layers.extend(layers)
    for tol in range(margin):
        layers = _make_layers(
            packages,
            uld,
            rejection_threshold,
            weight_ratio_threshold,
            tol + 1,
        )
        all_layers.extend(layers)

    return all_layers


def add_layer(
    env: Environment, layer: Layer, z_coordinate: int = 0, simulate: bool = False
):
    """
    Add a layer of packages to the environment
    """
    for rect in layer.rects:
        p1 = Point(rect.x, rect.y, z_coordinate)
        p2 = Point(rect.x + rect.dim.l, rect.y + rect.dim.w, z_coordinate + rect.dim.h)
        if not env.add_package(
            rect.id,
            layer.uld.id,
            (p1, p2),
            simulate=True,
            stability_check=False if z_coordinate == 0 else True,
        ):
            return False

    if simulate:
        return True

    for rect in layer.rects:
        p1 = Point(rect.x, rect.y, z_coordinate)
        p2 = Point(rect.x + rect.dim.l, rect.y + rect.dim.w, z_coordinate + rect.dim.h)
        env.add_package(
            rect.id,
            layer.uld.id,
            (p1, p2),
            gravity=(z_coordinate != 0),
            collision_check=False,
            stability_check=(z_coordinate != 0),
        )

    return True


def gensets(
    available_options,
    number_of_elements,
    sum_of_elements,
    current_set=None,
    all_sets=None,
):
    """
    Generate all possible sets of `number_of_elements` elements from `available_options` such that the sum of the elements in each set is equal to `sum_of_elements`.
    """
    if current_set is None:
        current_set = []
    if all_sets is None:
        all_sets = []

    if len(current_set) == number_of_elements and sum(current_set) == sum_of_elements:
        all_sets.append(list(current_set))
        return all_sets

    if len(current_set) >= number_of_elements or sum(current_set) > sum_of_elements:
        return all_sets

    for i in range(len(available_options)):
        current_set.append(available_options[i])
        gensets(
            available_options,
            number_of_elements,
            sum_of_elements,
            current_set,
            all_sets,
        )
        current_set.pop()

    return all_sets
