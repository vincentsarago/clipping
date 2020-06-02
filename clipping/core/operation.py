from abc import (ABC,
                 abstractmethod)
from collections import defaultdict
from itertools import (combinations,
                       groupby,
                       starmap)
from numbers import Rational
from operator import attrgetter
from typing import (DefaultDict,
                    List,
                    Optional,
                    Sequence,
                    Type,
                    Union as Union_)

from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)
from robust.linear import (SegmentsRelationship,
                           segments_intersection,
                           segments_relationship)

from clipping.hints import (Contour,
                            Mix,
                            Multipolygon,
                            Point,
                            Segment)
from .enums import EdgeType
from .event import Event
from .events_queue import (EventsQueue,
                           EventsQueueKey)
from .sweep_line import SweepLine
from .utils import (all_equal,
                    are_bounding_boxes_disjoint,
                    flatten,
                    multipolygon_to_bounding_box,
                    to_first_boundary_vertex,
                    to_multipolygon_x_max,
                    to_polygons_base,
                    to_polygons_contours,
                    to_rational_multipolygon,
                    to_segments)


class Operation(ABC):
    __slots__ = 'operands', '_events_queue'

    def __init__(self,
                 operands: Sequence[Multipolygon]) -> None:
        self.operands = operands
        self._events_queue = EventsQueue()

    __repr__ = generate_repr(__init__)

    def compute(self) -> Multipolygon:
        return events_to_multipolygon(self.sweep())

    def sweep(self) -> List[Event]:
        self.fill_queue()
        result = []
        sweep_line = SweepLine()
        while self._events_queue:
            self.process_event(self._events_queue.pop(), result, sweep_line)
        return result

    def fill_queue(self) -> None:
        for operand_id, operand in enumerate(self.operands):
            for contour in to_polygons_contours(operand):
                for segment in to_segments(contour):
                    self.register_segment(segment, operand_id)

    def register_segment(self, segment: Segment, operand_id: int) -> None:
        start, end = sorted(segment)
        start_event = Event(False, start, None, operand_id)
        end_event = Event(True, end, start_event, operand_id)
        start_event.complement = end_event
        self._events_queue.push(start_event)
        self._events_queue.push(end_event)

    def process_event(self, event: Event, processed_events: List[Event],
                      sweep_line: SweepLine) -> None:
        start_x, _ = event.start
        sweep_line.move_to(start_x)
        if event.is_right_endpoint:
            processed_events.append(event)
            event = event.complement
            if event in sweep_line:
                above_event, below_event = (sweep_line.above(event),
                                            sweep_line.below(event))
                sweep_line.remove(event)
                if above_event is not None and below_event is not None:
                    self.detect_intersection(below_event, above_event)
        elif event not in sweep_line:
            processed_events.append(event)
            sweep_line.add(event)
            above_event, below_event = (sweep_line.above(event),
                                        sweep_line.below(event))
            self.compute_fields(event, below_event)
            if (above_event is not None
                    and self.detect_intersection(event, above_event)):
                self.compute_fields(event, below_event)
                self.compute_fields(above_event, event)
            if (below_event is not None
                    and self.detect_intersection(below_event, event)):
                below_below_event = sweep_line.below(below_event)
                self.compute_fields(below_event, below_below_event)
                self.compute_fields(event, below_event)

    def compute_fields(self, event: Event, below_event: Optional[Event]
                       ) -> None:
        if below_event is None:
            event.in_out = False
            event.other_in_out = True
        else:
            if event.operand_id == below_event.operand_id:
                event.in_out = not below_event.in_out
                event.other_in_out = below_event.other_in_out
            else:
                event.in_out = not below_event.other_in_out
                event.other_in_out = (not below_event.in_out
                                      if below_event.is_vertical
                                      else below_event.in_out)
            event.below_in_result_event = (below_event.below_in_result_event
                                           if (not self.in_result(below_event)
                                               or below_event.is_vertical)
                                           else below_event)
        event.in_result = self.in_result(event)

    @abstractmethod
    def in_result(self, event: Event) -> bool:
        """Detects if event will be presented in result of the operation."""

    def detect_intersection(self, below_event: Event, event: Event) -> int:
        below_segment, segment = below_event.segment, event.segment
        relationship = segments_relationship(below_segment, segment)
        if relationship is SegmentsRelationship.OVERLAP:
            # segments overlap
            if below_event.operand_id == event.operand_id:
                raise ValueError('Edges of the same multipolygon '
                                 'should not overlap.')
            starts_equal = below_event.start == event.start
            if starts_equal:
                start_min = start_max = None
            elif EventsQueueKey(event) < EventsQueueKey(below_event):
                start_min, start_max = event, below_event
            else:
                start_min, start_max = below_event, event

            ends_equal = event.end == below_event.end
            if ends_equal:
                end_min = end_max = None
            elif (EventsQueueKey(event.complement)
                  < EventsQueueKey(below_event.complement)):
                end_min, end_max = event.complement, below_event.complement
            else:
                end_min, end_max = below_event.complement, event.complement

            if starts_equal:
                # both line segments are equal or share the left endpoint
                below_event.edge_type = EdgeType.NON_CONTRIBUTING
                event.edge_type = (EdgeType.SAME_TRANSITION
                                   if event.in_out is below_event.in_out
                                   else EdgeType.DIFFERENT_TRANSITION)
                if not ends_equal:
                    self.divide_segment(end_max.complement, end_min.start)
                return True
            elif ends_equal:
                # the line segments share the right endpoint
                self.divide_segment(start_min, start_max.start)
            elif start_min is end_max.complement:
                # one line segment includes the other one
                self.divide_segment(start_min, end_min.start)
                self.divide_segment(start_min, start_max.start)
            else:
                # no line segment includes the other one
                self.divide_segment(start_max, end_min.start)
                self.divide_segment(start_min, start_max.start)
        elif (relationship is not SegmentsRelationship.NONE
              and event.start != below_event.start
              and event.end != below_event.end):
            # segments do not intersect at endpoints
            point = segments_intersection(below_segment, segment)
            if point != below_event.start and point != below_event.end:
                self.divide_segment(below_event, point)
            if point != event.start and point != event.end:
                self.divide_segment(event, point)
        return False

    def divide_segment(self, event: Event, point: Point) -> None:
        left_event = Event(False, point, event.complement, event.operand_id)
        right_event = Event(True, point, event, event.operand_id)
        event.complement.complement, event.complement = left_event, right_event
        self._events_queue.push(left_event)
        self._events_queue.push(right_event)


class Difference(Operation):
    __slots__ = ()

    def sweep(self) -> List[Event]:
        self.fill_queue()
        result = []
        sweep_line = SweepLine()
        minuend_x_max = to_multipolygon_x_max(self.operands[0])
        while self._events_queue:
            event = self._events_queue.pop()
            start_x, _ = event.start
            if start_x > minuend_x_max:
                break
            self.process_event(event, result, sweep_line)
        return result

    def in_result(self, event: Event) -> bool:
        edge_type = event.edge_type
        return (edge_type is EdgeType.NORMAL
                and (event.operand_id == 0) is event.other_in_out
                or edge_type is EdgeType.DIFFERENT_TRANSITION)


class Intersection(Operation):
    __slots__ = ()

    def sweep(self) -> List[Event]:
        self.fill_queue()
        result = []
        sweep_line = SweepLine()
        min_max_x = min(map(to_multipolygon_x_max, self.operands))
        while self._events_queue:
            event = self._events_queue.pop()
            start_x, _ = event.start
            if start_x > min_max_x:
                break
            self.process_event(event, result, sweep_line)
        return result

    def in_result(self, event: Event) -> bool:
        edge_type = event.edge_type
        return (edge_type is EdgeType.NORMAL and not event.other_in_out
                or edge_type is EdgeType.SAME_TRANSITION)


class CompleteIntersection(Intersection):
    __slots__ = ()

    def compute(self) -> Mix:
        events = sorted(self.sweep(),
                        key=EventsQueueKey)
        multipoint, multisegment = [], []
        for start, same_start_events in groupby(events,
                                                key=attrgetter('start')):
            same_start_events = list(same_start_events)
            if (all(event.is_right_endpoint or not event.in_result
                    for event in same_start_events)
                    and not all_equal(event.operand_id
                                      for event in same_start_events)):
                no_segment_found = True
                for event, next_event in zip(same_start_events,
                                             same_start_events[1:]):
                    if (event.operand_id != next_event.operand_id
                            and event.segment == next_event.segment):
                        no_segment_found = False
                        if not event.is_right_endpoint:
                            multisegment.append(next_event.segment)
                if no_segment_found:
                    multipoint.append(start)
        multipolygon = events_to_multipolygon(events)
        return multipoint, multisegment, multipolygon


class SymmetricDifference(Operation):
    __slots__ = ()

    def in_result(self, event: Event) -> bool:
        return event.edge_type is EdgeType.NORMAL


class Union(Operation):
    __slots__ = ()

    def in_result(self, event: Event) -> bool:
        edge_type = event.edge_type
        return (edge_type is EdgeType.NORMAL and event.other_in_out
                or edge_type is EdgeType.SAME_TRANSITION)


def compute(operation: Type[Operation],
            operands: Sequence[Multipolygon],
            accurate: bool) -> Union_[Mix, Multipolygon]:
    """
    Returns result of given operation using optimizations for degenerate cases.

    :param operation: type of operation to perform.
    :param operands: operation arguments.
    :param accurate:
        flag that tells whether to use slow but more accurate arithmetic
        for floating point numbers.
    :returns: result of operation on operands.
    """
    if not any(operands):
        return (([], [], [])
                if operation is CompleteIntersection
                else [])
    elif not all(operands):
        # at least one of the arguments is empty
        if operation is Difference:
            return operands[0]
        elif operation is Union or operation is SymmetricDifference:
            operands = tuple(filter(None, operands))
        else:
            return (([], [], [])
                    if operation is CompleteIntersection
                    else [])
    if len(operands) == 1:
        return (([], [], operands[0])
                if operation is CompleteIntersection
                else operands[0])
    if all(starmap(are_bounding_boxes_disjoint,
                   combinations(map(multipolygon_to_bounding_box, operands),
                                2))):
        if operation is Difference:
            return operands[0]
        elif operation is Union or operation is SymmetricDifference:
            return sorted(flatten(operands),
                          key=to_first_boundary_vertex)
        else:
            return (([], [], [])
                    if operation is CompleteIntersection
                    else [])
    if (accurate
            and not issubclass(to_polygons_base(flatten(operands)),
                               Rational)):
        operands = tuple(map(to_rational_multipolygon, operands))
    return operation(operands).compute()


def events_to_multipolygon(events: List[Event]) -> Multipolygon:
    are_internal = defaultdict(bool)
    holes = defaultdict(list)
    return _contours_to_multipolygon(
            _events_to_contours(_collect_events(events), are_internal, holes),
            are_internal, holes)


def _collect_events(events: List[Event]) -> List[Event]:
    result = sorted(
            [event
             for event in events
             if not event.is_right_endpoint and event.in_result
             or event.is_right_endpoint and event.complement.in_result],
            key=EventsQueueKey)
    for index, event in enumerate(result):
        event.position = index
        if event.is_right_endpoint:
            event.position, event.complement.position = (
                event.complement.position, event.position)
    return result


def _contours_to_multipolygon(contours: List[Contour],
                              are_internal: DefaultDict[int, bool],
                              holes: DefaultDict[int, List[int]]
                              ) -> Multipolygon:
    result = []
    for index, contour in enumerate(contours):
        if not are_internal[index]:
            result.append((contour, [contours[hole_index]
                                     for hole_index in holes[index]]))
        else:
            # hole of a hole is an external polygon
            result.extend((contours[hole_index],
                           [contours[hole_hole_index]
                            for hole_hole_index in holes[hole_index]])
                          for hole_index in holes[index])
    return result


def _events_to_contours(events: List[Event],
                        are_internal: DefaultDict[int, bool],
                        holes: DefaultDict[int, List[int]]) -> List[Contour]:
    depths, parents = defaultdict(int), {}
    processed = [False] * len(events)
    contours = []
    for index, event in enumerate(events):
        if processed[index]:
            continue

        position = index
        initial = event.start
        contour = [initial]
        steps = [event]
        while position >= index:
            step = events[position]
            if step.end == initial:
                break
            processed[position] = True
            steps.append(step)
            position = step.position
            processed[position] = True
            contour.append(events[position].start)
            position = _to_next_position(position, events, processed, index)
        position = index if position == -1 else position
        last_event = events[position]
        processed[position] = processed[last_event.position] = True

        _shrink_collinear_vertices(contour)
        if len(contour) < 3:
            continue

        contour_id = len(contours)

        is_internal = False
        if event.below_in_result_event is not None:
            below_in_result_contour_id = event.below_in_result_event.contour_id
            if not event.below_in_result_event.result_in_out:
                holes[below_in_result_contour_id].append(contour_id)
                parents[contour_id] = below_in_result_contour_id
                depths[contour_id] = depths[below_in_result_contour_id] + 1
                is_internal = True
            elif are_internal[below_in_result_contour_id]:
                below_in_result_parent_id = parents[below_in_result_contour_id]
                holes[below_in_result_parent_id].append(contour_id)
                parents[contour_id] = below_in_result_parent_id
                depths[contour_id] = depths[below_in_result_contour_id]
                is_internal = True
        are_internal[contour_id] = is_internal

        for step in steps:
            if step.is_right_endpoint:
                step.complement.result_in_out = True
                step.complement.contour_id = contour_id
            else:
                step.result_in_out = False
                step.contour_id = contour_id
        last_event.complement.result_in_out = True
        last_event.complement.contour_id = contour_id

        if depths[contour_id] & 1:
            # holes will be in clockwise order
            contour.reverse()

        contours.append(contour)
    return contours


def _shrink_collinear_vertices(contour: Contour) -> None:
    self_intersections, visited = set(), set()
    visit = visited.add
    for vertex in contour:
        if vertex in visited:
            self_intersections.add(vertex)
        else:
            visit(vertex)
    index = -len(contour) + 1
    while index < 0:
        while (max(2, -index) < len(contour)
               and contour[index + 1] not in self_intersections
               and (orientation(contour[index + 2], contour[index + 1],
                                contour[index])
                    is Orientation.COLLINEAR)):
            del contour[index + 1]
        index += 1
    while index < len(contour):
        while (max(2, index) < len(contour)
               and contour[index - 1] not in self_intersections
               and (orientation(contour[index - 2], contour[index - 1],
                                contour[index])
                    is Orientation.COLLINEAR)):
            del contour[index - 1]
        index += 1


def _to_next_position(position: int,
                      events: List[Event],
                      processed: List[bool],
                      original_index: int) -> int:
    result = position + 1
    point = events[position].start
    while result < len(events) and events[result].start == point:
        if not processed[result]:
            return result
        else:
            result += 1
    result = position - 1
    while result >= original_index and processed[result]:
        result -= 1
    return result
