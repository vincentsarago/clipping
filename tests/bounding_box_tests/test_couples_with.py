from hypothesis import given
from orient.planar import (Relation,
                           contour_in_contour,
                           region_in_region)

from clipping.core.bounding_box import (coupled_with,
                                        to_vertices)
from clipping.core.hints import BoundingBox
from tests.utils import (BoundingBoxesPair,
                         equivalence)
from . import strategies


@given(strategies.bounding_boxes_pairs)
def test_basic(bounding_boxes_pair: BoundingBoxesPair) -> None:
    left_bounding_box, right_bounding_box = bounding_boxes_pair

    result = coupled_with(left_bounding_box, right_bounding_box)

    assert isinstance(result, bool)


@given(strategies.bounding_boxes)
def test_reflexivity(bounding_box: BoundingBox) -> None:
    assert coupled_with(bounding_box, bounding_box)


@given(strategies.bounding_boxes_pairs)
def test_symmetry(bounding_boxes_pair: BoundingBoxesPair) -> None:
    left_bounding_box, right_bounding_box = bounding_boxes_pair

    assert (coupled_with(left_bounding_box, right_bounding_box)
            is coupled_with(right_bounding_box, left_bounding_box))


@given(strategies.bounding_boxes_pairs)
def test_equivalents(bounding_boxes_pair: BoundingBoxesPair) -> None:
    left_bounding_box, right_bounding_box = bounding_boxes_pair

    result = coupled_with(left_bounding_box, right_bounding_box)

    left_bounding_box_vertices = to_vertices(left_bounding_box)
    right_bounding_box_vertices = to_vertices(right_bounding_box)
    relation = region_in_region(left_bounding_box_vertices,
                                right_bounding_box_vertices)
    assert equivalence(result,
                       relation in (Relation.OVERLAP,
                                    Relation.COVER,
                                    Relation.ENCLOSES,
                                    Relation.EQUAL,
                                    Relation.ENCLOSED,
                                    Relation.WITHIN)
                       or relation is Relation.TOUCH
                       and (contour_in_contour(left_bounding_box_vertices,
                                               right_bounding_box_vertices)
                            is Relation.OVERLAP))