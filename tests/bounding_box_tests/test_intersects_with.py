from hypothesis import given
from orient.planar import (Relation,
                           region_in_region)

from clipping.core.bounding_box import (disjoint_with,
                                        intersects_with,
                                        overlaps_with,
                                        to_vertices,
                                        touches_with)
from clipping.hints import BoundingBox
from tests.utils import BoundingBoxesPair
from . import strategies


@given(strategies.bounding_boxes_pairs)
def test_basic(bounding_boxes_pair: BoundingBoxesPair) -> None:
    left_bounding_box, right_bounding_box = bounding_boxes_pair

    result = intersects_with(left_bounding_box, right_bounding_box)

    assert isinstance(result, bool)


@given(strategies.bounding_boxes)
def test_reflexivity(bounding_box: BoundingBox) -> None:
    assert intersects_with(bounding_box, bounding_box)


@given(strategies.bounding_boxes_pairs)
def test_symmetry(bounding_boxes_pair: BoundingBoxesPair) -> None:
    left_bounding_box, right_bounding_box = bounding_boxes_pair

    assert (intersects_with(left_bounding_box, right_bounding_box)
            is intersects_with(right_bounding_box, left_bounding_box))


@given(strategies.bounding_boxes_pairs)
def test_equivalents(bounding_boxes_pair: BoundingBoxesPair) -> None:
    left_bounding_box, right_bounding_box = bounding_boxes_pair

    result = intersects_with(left_bounding_box, right_bounding_box)

    assert result is not disjoint_with(left_bounding_box, right_bounding_box)
    assert result is (touches_with(left_bounding_box, right_bounding_box)
                      or overlaps_with(left_bounding_box, right_bounding_box))
    assert result is (region_in_region(to_vertices(left_bounding_box),
                                       to_vertices(right_bounding_box))
                      is not Relation.DISJOINT)
