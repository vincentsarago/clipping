from typing import List

from hypothesis import given

from clipping.hints import Multipolygon
from clipping.planar import (intersect,
                             subtract,
                             symmetric_subtract,
                             unite)
from tests.utils import (MultipolygonsPair,
                         MultipolygonsTriplet,
                         are_multipolygons_similar,
                         is_multipolygon,
                         reverse_multipolygon,
                         reverse_multipolygon_borders,
                         reverse_multipolygon_holes,
                         reverse_multipolygon_holes_contours,
                         rotate_sequence)
from . import strategies


@given(strategies.multipolygons_lists)
def test_basic(multipolygons: List[Multipolygon]) -> None:
    result = unite(*multipolygons)

    assert is_multipolygon(result)


@given(strategies.empty_multipolygons_lists)
def test_degenerate(multipolygons: List[Multipolygon]) -> None:
    assert unite(*multipolygons) == []


@given(strategies.multipolygons)
def test_self(multipolygon: Multipolygon) -> None:
    assert unite(multipolygon) == multipolygon
    assert are_multipolygons_similar(unite(multipolygon, multipolygon),
                                     multipolygon)


@given(strategies.empty_multipolygons_with_multipolygons)
def test_left_neutral_element(empty_multipolygon_with_multipolygon
                              : MultipolygonsPair) -> None:
    empty_multipolygon, multipolygon = empty_multipolygon_with_multipolygon

    result = unite(empty_multipolygon, multipolygon)

    assert are_multipolygons_similar(result, multipolygon)


@given(strategies.empty_multipolygons_with_multipolygons)
def test_right_neutral_element(empty_multipolygon_with_multipolygon
                               : MultipolygonsPair) -> None:
    empty_multipolygon, multipolygon = empty_multipolygon_with_multipolygon

    result = unite(multipolygon, empty_multipolygon)

    assert are_multipolygons_similar(result, multipolygon)


@given(strategies.multipolygons_pairs)
def test_absorption_identity(multipolygons_pair: MultipolygonsPair) -> None:
    left_multipolygon, right_multipolygon = multipolygons_pair

    result = unite(left_multipolygon, intersect(left_multipolygon,
                                                right_multipolygon))

    assert are_multipolygons_similar(result, left_multipolygon)


@given(strategies.multipolygons_pairs)
def test_commutativity(multipolygons_pair: MultipolygonsPair) -> None:
    left_multipolygon, right_multipolygon = multipolygons_pair

    result = unite(left_multipolygon, right_multipolygon)

    assert result == unite(right_multipolygon, left_multipolygon)


@given(strategies.multipolygons_triplets)
def test_associativity(multipolygons_triplet: MultipolygonsTriplet) -> None:
    (left_multipolygon, mid_multipolygon,
     right_multipolygon) = multipolygons_triplet

    result = unite(unite(left_multipolygon, mid_multipolygon),
                   right_multipolygon)

    assert are_multipolygons_similar(result,
                                     unite(left_multipolygon,
                                           unite(mid_multipolygon,
                                                 right_multipolygon)))


@given(strategies.multipolygons_triplets)
def test_difference_operand(multipolygons_triplet: MultipolygonsTriplet
                            ) -> None:
    (left_multipolygon, mid_multipolygon,
     right_multipolygon) = multipolygons_triplet

    result = unite(subtract(left_multipolygon, mid_multipolygon),
                   right_multipolygon)

    assert are_multipolygons_similar(result,
                                     subtract(unite(left_multipolygon,
                                                    right_multipolygon),
                                              subtract(mid_multipolygon,
                                                       right_multipolygon)))


@given(strategies.multipolygons_triplets)
def test_distribution_over_intersection(multipolygons_triplet
                                        : MultipolygonsTriplet) -> None:
    (left_multipolygon, mid_multipolygon,
     right_multipolygon) = multipolygons_triplet

    result = unite(left_multipolygon, intersect(mid_multipolygon,
                                                right_multipolygon))

    assert are_multipolygons_similar(result,
                                     intersect(unite(left_multipolygon,
                                                     mid_multipolygon),
                                               unite(left_multipolygon,
                                                     right_multipolygon)))


@given(strategies.multipolygons_pairs)
def test_equivalents(multipolygons_pair: MultipolygonsPair) -> None:
    left_multipolygon, right_multipolygon = multipolygons_pair

    result = unite(left_multipolygon, right_multipolygon)

    assert result == symmetric_subtract(symmetric_subtract(left_multipolygon,
                                                           right_multipolygon),
                                        intersect(left_multipolygon,
                                                  right_multipolygon))


@given(strategies.non_empty_multipolygons_lists)
def test_reversals(multipolygons: List[Multipolygon]) -> None:
    first_multipolygon, *rest_multipolygons = multipolygons

    result = unite(first_multipolygon, *rest_multipolygons)

    assert are_multipolygons_similar(
            result, unite(reverse_multipolygon(first_multipolygon),
                          *rest_multipolygons))
    assert are_multipolygons_similar(
            result, unite(reverse_multipolygon_borders(first_multipolygon),
                          *rest_multipolygons))
    assert are_multipolygons_similar(
            result, unite(reverse_multipolygon_holes(first_multipolygon),
                          *rest_multipolygons))
    assert are_multipolygons_similar(
            result,
            unite(reverse_multipolygon_holes_contours(first_multipolygon),
                  *rest_multipolygons))


@given(strategies.multipolygons_lists)
def test_rotations(multipolygons: List[Multipolygon]) -> None:
    result = unite(*multipolygons)

    assert all(are_multipolygons_similar(result,
                                         unite(*rotate_sequence(multipolygons,
                                                                offset)))
               for offset in range(1, len(multipolygons)))
