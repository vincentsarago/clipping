from abc import (ABC,
                 abstractmethod)
from functools import partial
from typing import (Generic,
                    Optional)

from dendroid import red_black
from ground.base import (Context,
                         Orientation)
from reprit.base import generate_repr

from .event import (BinaryEvent,
                    Event,
                    NaryEvent)
from .hints import Orienteer
from .utils import orientation


class SweepLine(ABC, Generic[Event]):
    __slots__ = ()

    @abstractmethod
    def __contains__(self, event: Event) -> bool:
        """Checks if given event is in the sweep line."""

    @abstractmethod
    def above(self, event: Event) -> Optional[Event]:
        """Returns event which is above the given one."""

    @abstractmethod
    def add(self, event: Event) -> None:
        """Adds given event to the sweep line."""

    @abstractmethod
    def below(self, event: Event) -> Optional[Event]:
        """Returns event which is below the given one."""

    @abstractmethod
    def remove(self, event: Event) -> None:
        """Removes given event from the sweep line."""


class BinarySweepLine(SweepLine):
    __slots__ = 'context', '_ordered_set'

    def __init__(self, context: Context) -> None:
        self.context = context
        self._ordered_set = red_black.set_(key=partial(BinarySweepLineKey,
                                                       partial(orientation,
                                                               context)))

    def __contains__(self, event: Event) -> bool:
        return event in self._ordered_set

    def add(self, event: Event) -> None:
        self._ordered_set.add(event)

    def remove(self, event: Event) -> None:
        self._ordered_set.remove(event)

    def above(self, event: Event) -> Optional[Event]:
        try:
            return self._ordered_set.next(event)
        except ValueError:
            return None

    def below(self, event: Event) -> Optional[Event]:
        try:
            return self._ordered_set.prev(event)
        except ValueError:
            return None


class NarySweepLine(SweepLine):
    __slots__ = 'context', '_ordered_set'

    def __init__(self, context: Context) -> None:
        self.context = context
        self._ordered_set = red_black.set_(key=partial(NarySweepLineKey,
                                                       partial(orientation,
                                                               context)))

    def __contains__(self, event: Event) -> bool:
        return event in self._ordered_set

    def add(self, event: Event) -> None:
        self._ordered_set.add(event)

    def remove(self, event: Event) -> None:
        self._ordered_set.remove(event)

    def above(self, event: Event) -> Optional[Event]:
        try:
            return self._ordered_set.next(event)
        except ValueError:
            return None

    def below(self, event: Event) -> Optional[Event]:
        try:
            return self._ordered_set.prev(event)
        except ValueError:
            return None


class BinarySweepLineKey:
    __slots__ = 'event', 'orienteer'

    def __init__(self, orienteer: Orienteer, event: BinaryEvent) -> None:
        self.orienteer, self.event = orienteer, event

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'BinarySweepLineKey') -> bool:
        """
        Checks if the segment (or at least the point) associated with event
        is lower than other's.
        """
        event, other_event = self.event, other.event
        if event is other_event:
            return False
        start, other_start = event.start, other_event.start
        end, other_end = event.end, other_event.end
        other_start_orientation = self.orienteer(end, start, other_start)
        other_end_orientation = self.orienteer(end, start, other_end)
        if other_start_orientation is other_end_orientation:
            start_x, start_y = start
            other_start_x, other_start_y = other_start
            if other_start_orientation is not Orientation.COLLINEAR:
                # other segment fully lies on one side
                return other_start_orientation is Orientation.COUNTERCLOCKWISE
            # segments are collinear
            elif event.from_left is not other_event.from_left:
                return event.from_left
            elif start_x == other_start_x:
                end_x, end_y = end
                other_end_x, other_end_y = other_end
                if start_y != other_start_y:
                    # segments are vertical
                    return start_y < other_start_y
                # segments have same start
                elif end_y != other_end_y:
                    return end_y < other_end_y
                else:
                    # segments are horizontal
                    return end_x < other_end_x
            elif start_y != other_start_y:
                return start_y < other_start_y
            else:
                # segments are horizontal
                return start_x < other_start_x
        start_orientation = self.orienteer(other_end, other_start, start)
        end_orientation = self.orienteer(other_end, other_start, end)
        if start_orientation is end_orientation:
            return start_orientation is Orientation.CLOCKWISE
        elif other_start_orientation is Orientation.COLLINEAR:
            return other_end_orientation is Orientation.COUNTERCLOCKWISE
        elif start_orientation is Orientation.COLLINEAR:
            return end_orientation is Orientation.CLOCKWISE
        elif end_orientation is Orientation.COLLINEAR:
            return start_orientation is Orientation.CLOCKWISE
        else:
            return other_start_orientation is Orientation.COUNTERCLOCKWISE


class NarySweepLineKey:
    __slots__ = 'event', 'orienteer'

    def __init__(self, orienteer: Orienteer, event: NaryEvent) -> None:
        self.orienteer, self.event = orienteer, event

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'NarySweepLineKey') -> bool:
        """
        Checks if the segment (or at least the point) associated with event
        is lower than other's.
        """
        event, other_event = self.event, other.event
        if event is other_event:
            return False
        start, other_start = event.start, other_event.start
        end, other_end = event.end, other_event.end
        other_start_orientation = self.orienteer(end, start, other_start)
        other_end_orientation = self.orienteer(end, start, other_end)
        if other_start_orientation is other_end_orientation:
            start_x, start_y = start
            other_start_x, other_start_y = other_start
            if other_start_orientation is not Orientation.COLLINEAR:
                # other segment fully lies on one side
                return other_start_orientation is Orientation.COUNTERCLOCKWISE
            # segments are collinear
            elif start_x == other_start_x:
                end_x, end_y = end
                other_end_x, other_end_y = other_end
                if start_y != other_start_y:
                    # segments are vertical
                    return start_y < other_start_y
                # segments have same start
                elif end_y != other_end_y:
                    return end_y < other_end_y
                else:
                    # segments are horizontal
                    return end_x < other_end_x
            elif start_y != other_start_y:
                return start_y < other_start_y
            else:
                # segments are horizontal
                return start_x < other_start_x
        start_orientation = self.orienteer(other_end, other_start, start)
        end_orientation = self.orienteer(other_end, other_start, end)
        if start_orientation is end_orientation:
            return start_orientation is Orientation.CLOCKWISE
        elif other_start_orientation is Orientation.COLLINEAR:
            return other_end_orientation is Orientation.COUNTERCLOCKWISE
        elif start_orientation is Orientation.COLLINEAR:
            return end_orientation is Orientation.CLOCKWISE
        elif end_orientation is Orientation.COLLINEAR:
            return start_orientation is Orientation.CLOCKWISE
        else:
            return other_start_orientation is Orientation.COUNTERCLOCKWISE
