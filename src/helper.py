from entity import ULD, Package, Point
from environment import Environment


class helperTool:
    def __init__(self):
        pass
    def order(env):
        corners = [pkg.corner[0] for pkg in env.packages]
        corners.sort(key=lambda Point: Point.x)
        """
        Order the packages in the environment
        """
        