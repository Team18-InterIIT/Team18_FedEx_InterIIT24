import math


def rectangle_intersection(rect1, rect2):
    # Unpack rectangle coordinates
    x1_1, y1_1, x2_1, y2_1 = rect1[0].x, rect1[0].y, rect1[3].x, rect1[3].y
    x1_2, y1_2, x2_2, y2_2 = rect2[0].x, rect2[0].y, rect2[3].x, rect2[3].y

    # Find intersection coordinates
    x1_intersection = max(x1_1, x1_2)
    y1_intersection = max(y1_1, y1_2)
    x2_intersection = min(x2_1, x2_2)
    y2_intersection = min(y2_1, y2_2)

    # Return 4 points
    return [
        (x1_intersection, y1_intersection),
        (x2_intersection, y1_intersection),
        (x2_intersection, y2_intersection),
        (x1_intersection, y2_intersection),
    ]


def cross_product(p1, p2, p3):
    return (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])


def distance_squared(p1, p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


def graham_scan(points):
    # Handle trivial cases
    if len(points) <= 3:
        return points

    # Remove duplicates
    points = list(set(points))

    # Find the bottom-most point (and left-most if tied)
    start = min(points, key=lambda p: (p[1], p[0]))

    # Sort points by polar angle with respect to start point
    sorted_points = sorted(
        points,
        key=lambda p: (
            math.atan2(p[1] - start[1], p[0] - start[0]),
            distance_squared(start, p),
        ),
    )

    # Initialize convex hull with first three points
    hull = [start]
    for point in sorted_points:
        if point != start:
            while len(hull) > 1 and cross_product(hull[-2], hull[-1], point) <= 0:
                hull.pop()
            hull.append(point)

    return hull


def is_point_in_convex_hull(points, test_point):
    # Remove duplicates and handle edge cases
    points = list(set(points))

    # Check if the point is one of the input points
    if test_point in points:
        return True

    # Construct convex hull
    convex_hull = graham_scan(points)

    # Handle cases with few points
    if len(convex_hull) <= 2:
        return False

    # Check if point is outside the convex hull
    for i in range(len(convex_hull)):
        # Take two consecutive points from the convex hull
        p1 = convex_hull[i]
        p2 = convex_hull[(i + 1) % len(convex_hull)]

        # Cross product value
        cp = cross_product(p1, p2, test_point)

        # If strictly right turn, point is outside
        if cp < -1e-10:  # Use small epsilon to handle floating point imprecision
            return False

        # Check if point is on the boundary
        if abs(cp) <= 1e-10:
            # Check if point is within the segment
            if min(p1[0], p2[0]) <= test_point[0] <= max(p1[0], p2[0]) and min(
                p1[1], p2[1]
            ) <= test_point[1] <= max(p1[1], p2[1]):
                return True

    return True
