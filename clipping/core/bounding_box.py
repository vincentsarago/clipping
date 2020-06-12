from typing import (Iterable,
                    Sequence)

from robust.angular import (Orientation,
                            orientation)
from robust.linear import (SegmentsRelationship,
                           segment_contains,
                           segments_relationship)

from clipping.hints import (BoundingBox,
                            Contour,
                            Multipolygon,
                            Multisegment,
                            Point,
                            Polygon,
                            Segment)
from .enums import Location
from .utils import (contour_orientation,
                    contour_to_segments,
                    flatten,
                    indexed_point_in_region,
                    point_in_region)


def from_points(points: Iterable[Point]) -> BoundingBox:
    """
    Builds bounding box from points.
    """
    points = iter(points)
    x_min, y_min = x_max, y_max = next(points)
    for x, y in points:
        x_min, x_max = min(x_min, x), max(x_max, x)
        y_min, y_max = min(y_min, y), max(y_max, y)
    return x_min, x_max, y_min, y_max


def from_multisegment(multisegment: Multisegment) -> BoundingBox:
    """
    Builds bounding box from multisegment.
    """
    return from_points(flatten(multisegment))


def from_multipolygon(multipolygon: Multipolygon) -> BoundingBox:
    """
    Builds bounding box from multipolygon.
    """
    return from_points(flatten(border for border, _ in multipolygon))


def from_polygon(polygon: Polygon) -> BoundingBox:
    """
    Builds bounding box from polygon.
    """
    border, _ = polygon
    return from_points(border)


def disjoint_with(left: BoundingBox, right: BoundingBox) -> bool:
    """
    Checks if bounding boxes do not intersect.

    >>> disjoint_with((0, 2, 0, 2), (0, 2, 0, 2))
    False
    >>> disjoint_with((0, 2, 0, 2), (1, 3, 1, 3))
    False
    >>> disjoint_with((0, 2, 0, 2), (2, 4, 0, 2))
    False
    >>> disjoint_with((0, 2, 0, 2), (2, 4, 2, 4))
    False
    >>> disjoint_with((0, 2, 0, 2), (2, 4, 3, 5))
    True
    """
    left_x_min, left_x_max, left_y_min, left_y_max = left
    right_x_min, right_x_max, right_y_min, right_y_max = right
    return (left_x_min > right_x_max or left_x_max < right_x_min
            or left_y_min > right_y_max or left_y_max < right_y_min)


def intersects_with(left: BoundingBox, right: BoundingBox) -> bool:
    """
    Checks if bounding boxes intersect.

    >>> intersects_with((0, 2, 0, 2), (0, 2, 0, 2))
    True
    >>> intersects_with((0, 2, 0, 2), (1, 3, 1, 3))
    True
    >>> intersects_with((0, 2, 0, 2), (2, 4, 0, 2))
    True
    >>> intersects_with((0, 2, 0, 2), (2, 4, 2, 4))
    True
    >>> intersects_with((0, 2, 0, 2), (2, 4, 3, 5))
    False
    """
    left_x_min, left_x_max, left_y_min, left_y_max = left
    right_x_min, right_x_max, right_y_min, right_y_max = right
    return (right_x_min <= left_x_max and left_x_min <= right_x_max
            and right_y_min <= left_y_max and left_y_min <= right_y_max)


def overlaps_with(left: BoundingBox, right: BoundingBox) -> bool:
    """
    Checks if bounding boxes intersect in some region.

    >>> overlaps_with((0, 2, 0, 2), (0, 2, 0, 2))
    True
    >>> overlaps_with((0, 2, 0, 2), (1, 3, 1, 3))
    True
    >>> overlaps_with((0, 2, 0, 2), (2, 4, 0, 2))
    False
    >>> overlaps_with((0, 2, 0, 2), (2, 4, 2, 4))
    False
    >>> overlaps_with((0, 2, 0, 2), (2, 4, 3, 5))
    False
    """
    return intersects_with(left, right) and not touches_with(left, right)


def touches_with(left: BoundingBox, right: BoundingBox) -> bool:
    """
    Checks if bounding boxes intersect at point or by the edge.

    >>> touches_with((0, 2, 0, 2), (0, 2, 0, 2))
    False
    >>> touches_with((0, 2, 0, 2), (1, 3, 1, 3))
    False
    >>> touches_with((0, 2, 0, 2), (2, 4, 0, 2))
    True
    >>> touches_with((0, 2, 0, 2), (2, 4, 2, 4))
    True
    >>> touches_with((0, 2, 0, 2), (2, 4, 3, 5))
    False
    """
    left_x_min, left_x_max, left_y_min, left_y_max = left
    right_x_min, right_x_max, right_y_min, right_y_max = right
    return ((left_x_min == right_x_max or left_x_max == right_x_min)
            and (left_y_min <= right_y_max and right_y_min <= left_y_max)
            or (left_x_min <= right_x_max and right_x_min <= left_x_max)
            and (left_y_min == right_y_max or right_y_min == left_y_max))


def is_subset_of(test: BoundingBox, goal: BoundingBox) -> bool:
    """
    Checks if the bounding box is the subset of the other.

    >>> is_subset_of((0, 2, 0, 2), (0, 2, 0, 2))
    True
    >>> is_subset_of((0, 2, 0, 2), (1, 3, 1, 3))
    False
    >>> is_subset_of((0, 2, 0, 2), (2, 4, 0, 2))
    False
    >>> is_subset_of((0, 2, 0, 2), (2, 4, 2, 4))
    False
    >>> is_subset_of((0, 2, 0, 2), (2, 4, 3, 5))
    False
    """
    test_x_min, test_x_max, test_y_min, test_y_max = test
    goal_x_min, goal_x_max, goal_y_min, goal_y_max = goal
    return (goal_x_min <= test_x_min and test_x_max <= goal_x_max
            and goal_y_min <= test_y_min and test_y_max <= goal_y_max)


def within_of(test: BoundingBox, goal: BoundingBox) -> bool:
    """
    Checks if the bounding box is contained in an interior of the other.

    >>> within_of((0, 2, 0, 2), (0, 2, 0, 2))
    False
    >>> within_of((0, 2, 0, 2), (1, 3, 1, 3))
    False
    >>> within_of((0, 2, 0, 2), (2, 4, 0, 2))
    False
    >>> within_of((0, 2, 0, 2), (2, 4, 2, 4))
    False
    >>> within_of((0, 2, 0, 2), (2, 4, 3, 5))
    False
    """
    test_x_min, test_x_max, test_y_min, test_y_max = test
    goal_x_min, goal_x_max, goal_y_min, goal_y_max = goal
    return (goal_x_min < test_x_min and test_x_max < goal_x_max
            and goal_y_min < test_y_min and test_y_max < goal_y_max)


def intersects_with_segment(bounding_box: BoundingBox,
                            segment: Segment) -> bool:
    """
    Checks if the bounding box intersects the segment.
    """
    segment_bounding_box = from_points(segment)
    return (intersects_with(segment_bounding_box, bounding_box)
            and (is_subset_of(segment_bounding_box, bounding_box)
                 or any(segments_relationship(edge, segment)
                        is not SegmentsRelationship.NONE
                        for edge in to_segments(bounding_box))))


def overlaps_with_segment(bounding_box: BoundingBox,
                          segment: Segment) -> bool:
    """
    Checks if the bounding box intersects the segment at more than one point.
    """
    segment_bounding_box = from_points(segment)
    return (intersects_with(segment_bounding_box, bounding_box)
            and (is_subset_of(segment_bounding_box, bounding_box)
                 or any(segments_relationship(edge, segment)
                        not in (SegmentsRelationship.TOUCH,
                                SegmentsRelationship.NONE)
                        for edge in to_segments(bounding_box))))


def intersects_with_polygon(bounding_box: BoundingBox,
                            polygon: Polygon) -> bool:
    """
    Checks if the bounding box intersects the polygon.
    """
    border, holes = polygon
    polygon_bounding_box = from_points(border)
    return (intersects_with(polygon_bounding_box, bounding_box)
            and (is_subset_of(polygon_bounding_box, bounding_box)
                 or any(contains_point(bounding_box, vertex)
                        for vertex in border)
                 or within_of(bounding_box, polygon_bounding_box)
                 and within_of_region(bounding_box, border)
                 and not any(within_of(bounding_box, from_points(hole))
                             and within_of_region(bounding_box, hole)
                             for hole in holes)
                 or any(point_in_region(vertex, border)
                        is not Location.EXTERIOR
                        for vertex in to_vertices(bounding_box))
                 or any(intersects_with_segment(bounding_box, border_edge)
                        for border_edge in contour_to_segments(border))))


def overlaps_with_polygon(bounding_box: BoundingBox, polygon: Polygon) -> bool:
    """
    Checks if the bounding box intersects the polygon in some region.
    """
    border, holes = polygon
    polygon_bounding_box = from_points(border)
    if not overlaps_with(polygon_bounding_box, bounding_box):
        return False
    elif (is_subset_of(polygon_bounding_box, bounding_box)
          or any(covers_point(bounding_box, vertex)
                 for vertex in border)):
        return True
    elif (any(point_in_region(vertex, border) is Location.INTERIOR
              for vertex in to_vertices(bounding_box))
          or is_subset_of(bounding_box, polygon_bounding_box)
          and is_subset_of_region(bounding_box, border)):
        return not any(is_subset_of(bounding_box, from_points(hole))
                       and is_subset_of_region(bounding_box, hole)
                       for hole in holes)
    else:
        return (any(segments_relationship(edge, border_edge)
                    is SegmentsRelationship.CROSS
                    for edge in to_segments(bounding_box)
                    for border_edge in contour_to_segments(border))
                or _any_segment_in_region(to_segments(bounding_box), border))


def _any_segment_in_region(segments: Iterable[Segment],
                           border: Contour) -> bool:
    border_orientation = contour_orientation(border)
    return any(_segment_orientation_with_point(edge, end) is border_orientation
               for start, end in segments
               for edge in contour_to_segments(border)
               if segment_contains(edge, start))


def _segment_orientation_with_point(segment: Segment,
                                    point: Point) -> Orientation:
    start, end = segment
    return orientation(end, start, point)


def contains_point(bounding_box: BoundingBox, point: Point) -> bool:
    x_min, x_max, y_min, y_max = bounding_box
    x, y = point
    return x_min <= x <= x_max and y_min <= y <= y_max


def covers_point(bounding_box: BoundingBox, point: Point) -> bool:
    x_min, x_max, y_min, y_max = bounding_box
    x, y = point
    return x_min < x < x_max and y_min < y < y_max


def is_subset_of_region(bounding_box: BoundingBox, border: Contour) -> bool:
    bounding_box_vertices = to_vertices(bounding_box)
    indexed_locations = [indexed_point_in_region(vertex, border)
                         for vertex in bounding_box_vertices]
    if not all(location for _, location in indexed_locations):
        return False
    else:
        border_orientation = contour_orientation(border)
        for index, (border_index, location) in enumerate(indexed_locations):
            if location is Location.BOUNDARY:
                prior_vertex, next_vertex = (bounding_box_vertices[index - 1],
                                             bounding_box_vertices[(index + 1)
                                                                   % 4])
                border_edge_start, border_edge_end = (border[border_index - 1],
                                                      border[border_index])
                vertex = bounding_box_vertices[index]
                if vertex == border_edge_start:
                    candidate = border[border_index - 2]
                    base_orientation = orientation(
                            candidate, border_edge_start, border_edge_end)
                    if (orientation(border_edge_start, candidate, prior_vertex)
                            not in (Orientation.COLLINEAR, base_orientation)
                            or orientation(border_edge_end, border_edge_start,
                                           next_vertex)
                            not in (Orientation.COLLINEAR, base_orientation)):
                        return False
                elif vertex == border_edge_end:
                    candidate = border[(border_index + 1) % len(border)]
                    base_orientation = orientation(
                            border_edge_start, border_edge_end, candidate)
                    if (orientation(border_edge_end, border_edge_start,
                                    prior_vertex)
                            not in (Orientation.COLLINEAR, base_orientation)
                            or orientation(candidate, border_edge_end,
                                           next_vertex)
                            not in (Orientation.COLLINEAR, base_orientation)):
                        return False
                elif (orientation(border_edge_end, border_edge_start,
                                  prior_vertex) * border_orientation < 0
                      or orientation(border_edge_end, border_edge_start,
                                     next_vertex) * border_orientation < 0):
                    return False
        return all(segments_relationship(edge, border_edge)
                   is not SegmentsRelationship.CROSS
                   for edge in to_segments(bounding_box)
                   for border_edge in contour_to_segments(border))


def within_of_region(bounding_box: BoundingBox, border: Contour) -> bool:
    return (all(point_in_region(vertex, border) is Location.INTERIOR
                for vertex in to_vertices(bounding_box))
            and all(segments_relationship(edge, border_edge)
                    is SegmentsRelationship.NONE
                    for edge in to_segments(bounding_box)
                    for border_edge in contour_to_segments(border)))


def to_vertices(bounding_box: BoundingBox) -> Sequence[Point]:
    x_min, x_max, y_min, y_max = bounding_box
    return (x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)


def to_segments(bounding_box: BoundingBox) -> Sequence[Segment]:
    x_min, x_max, y_min, y_max = bounding_box
    return (((x_min, y_min), (x_max, y_min)),
            ((x_max, y_min), (x_max, y_max)),
            ((x_min, y_max), (x_max, y_max)),
            ((x_min, y_min), (x_min, y_max)))


def to_intersecting_segments(bounding_box: BoundingBox,
                             multisegment: Multisegment) -> Multisegment:
    return [segment
            for segment in multisegment
            if intersects_with_segment(bounding_box, segment)]


def to_overlapping_segments(bounding_box: BoundingBox,
                            multisegment: Multisegment) -> Multisegment:
    return [segment
            for segment in multisegment
            if overlaps_with_segment(bounding_box, segment)]


def to_intersecting_polygons(bounding_box: BoundingBox,
                             multipolygon: Multipolygon) -> Multipolygon:
    return [polygon
            for polygon in multipolygon
            if intersects_with_polygon(bounding_box, polygon)]


def to_overlapping_polygons(bounding_box: BoundingBox,
                            multipolygon: Multipolygon) -> Multipolygon:
    return [polygon
            for polygon in multipolygon
            if overlaps_with_polygon(bounding_box, polygon)]
