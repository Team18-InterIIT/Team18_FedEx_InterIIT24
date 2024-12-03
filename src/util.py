from collections import deque, defaultdict
from entity import ULD, Package
from environment import Environment

class Util:
    def __init__(self, env: Environment):
        self.env = env
        self.uld_to_order = {}  # Dictionary to store the order of packages for each ULD

    def order(self):
        """
        This method orders the packages in the ULDs within the environment by their Z coordinates.
        It constructs the graph of dependencies between the packages (support relationships)
        and returns the topologically sorted order of packages for each ULD.
        """
        for uld in self.env.ULDs:
            self.uld_to_order[uld.id] = self.topological_sort(uld)
        return self.uld_to_order

    def do_rectangles_overlap(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Checks if two rectangles (defined by corner coordinates) overlap.
        """
        min_x1, max_x1 = min(x1, x2), max(x1, x2)
        min_y1, max_y1 = min(y1, y2), max(y1, y2)

        min_x2, max_x2 = min(x3, x4), max(x3, x4)
        min_y2, max_y2 = min(y3, y4), max(y3, y4)

        return max_x1 > min_x2 and min_x1 < max_x2 and max_y1 > min_y2 and min_y1 < max_y2

    def build_graph(self, uld: ULD):
        """
        Helper method to build the graph of dependencies (edges) for packages in a ULD.
        """
        graph = defaultdict(list)
        indegree = defaultdict(int)

        for package in uld.packages:
            graph[package.id] = []
            indegree[package.id] = 0

        # Sort the packages by their Z-coordinate
        sorted_packages = sorted(uld.packages, key=lambda p: p.corners[0].z)

        # Build the graph by checking overlap between packages
        for i, package_a in enumerate(sorted_packages):
            for package_b in sorted_packages[i+1:]:
                # Check if package_b is supported by package_a (overlap condition)
                if self.do_rectangles_overlap(
                    package_a.corners[0].x, package_a.corners[0].y, package_a.corners[1].x, package_a.corners[1].y, 
                    package_b.corners[0].x, package_b.corners[0].y, package_b.corners[1].x, package_b.corners[1].y
                ):
                    graph[package_a.id].append(package_b.id)
                    indegree[package_b.id] += 1
        return graph, indegree

    def topological_sort(self, uld: ULD):
        """
        Perform a topological sort on the ULD's package graph using the indegree method.
        The package with the smallest (x, y) is processed first when there are multiple packages with zero indegree.
        """
        # Build the graph and indegree mapping
        graph, indegree = self.build_graph(uld)

        # Initialize the queue with all packages that have zero indegree (no package supports them)
        queue = deque(pkg_id for pkg_id, degree in indegree.items() if degree == 0)

        # Create a dictionary to map package IDs to their corner coordinates
        package_id_to_corners = {pkg.id: pkg.corners for pkg in uld.packages}

        # Sort the initial queue based on (x, y) coordinates to prioritize the smallest (x, y)
        queue = deque(sorted(queue, key=lambda pkg_id: (package_id_to_corners[pkg_id][0].x, package_id_to_corners[pkg_id][0].y)))

        topo_order = []  # This will store the topologically sorted packages

        # Process the queue and perform topological sort
        while queue:
            package_id = queue.popleft()
            topo_order.append(package_id)

            # For each package supported by the current package, reduce its indegree
            for neighbor in graph[package_id]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
                    # Keep the queue sorted by (x, y) for the next iteration
            queue = deque(sorted(queue, key=lambda pkg_id: (package_id_to_corners[pkg_id][0].x, package_id_to_corners[pkg_id][0].y)))

        # If the length of topo_order is not equal to the number of packages, there is a cycle
        if len(topo_order) != len(indegree):
            print("Error: Cycle detected in the graph. Topological sort not possible.")
            return []

        return topo_order