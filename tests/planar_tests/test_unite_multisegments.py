from ground.hints import Multisegment
from hypothesis import given

from clipping.planar import (intersect_multisegments,
                             subtract_multisegments,
                             symmetric_subtract_multisegments,
                             unite_multisegments)
from tests.utils import (MultisegmentsPair,
                         MultisegmentsTriplet,
                         are_multisegments_equivalent,
                         are_multisegments_similar,
                         is_multisegment,
                         reverse_multisegment)
from . import strategies


@given(strategies.multisegments_pairs)
def test_basic(multisegments_pair: MultisegmentsPair) -> None:
    left_multisegment, right_multisegment = multisegments_pair

    result = unite_multisegments(left_multisegment, right_multisegment)

    assert is_multisegment(result)


@given(strategies.multisegments)
def test_idempotence(multisegment: Multisegment) -> None:
    result = unite_multisegments(multisegment, multisegment)

    assert are_multisegments_equivalent(result, multisegment)


@given(strategies.empty_multisegments_with_multisegments)
def test_left_neutral_element(empty_multisegment_with_multisegment
                              : MultisegmentsPair) -> None:
    empty_multisegment, multisegment = empty_multisegment_with_multisegment

    result = unite_multisegments(empty_multisegment, multisegment)

    assert are_multisegments_similar(result, multisegment)


@given(strategies.empty_multisegments_with_multisegments)
def test_right_neutral_element(empty_multisegment_with_multisegment
                               : MultisegmentsPair) -> None:
    empty_multisegment, multisegment = empty_multisegment_with_multisegment

    result = unite_multisegments(multisegment, empty_multisegment)

    assert are_multisegments_similar(result, multisegment)


@given(strategies.multisegments_pairs)
def test_absorption_identity(multisegments_pair: MultisegmentsPair) -> None:
    left_multisegment, right_multisegment = multisegments_pair

    result = unite_multisegments(left_multisegment,
                                 intersect_multisegments(left_multisegment,
                                                         right_multisegment))

    assert are_multisegments_equivalent(result, left_multisegment)


@given(strategies.multisegments_pairs)
def test_commutativity(multisegments_pair: MultisegmentsPair) -> None:
    left_multisegment, right_multisegment = multisegments_pair

    result = unite_multisegments(left_multisegment, right_multisegment)

    assert result == unite_multisegments(right_multisegment, left_multisegment)


@given(strategies.multisegments_triplets)
def test_associativity(multisegments_triplet: MultisegmentsTriplet) -> None:
    (left_multisegment, mid_multisegment,
     right_multisegment) = multisegments_triplet

    result = unite_multisegments(
            unite_multisegments(left_multisegment, mid_multisegment),
            right_multisegment)

    assert are_multisegments_similar(
            result,
            unite_multisegments(left_multisegment,
                                unite_multisegments(mid_multisegment,
                                                    right_multisegment)))


@given(strategies.rational_multisegments_triplets)
def test_difference_operand(multisegments_triplet: MultisegmentsTriplet
                            ) -> None:
    (left_multisegment, mid_multisegment,
     right_multisegment) = multisegments_triplet

    result = unite_multisegments(
            subtract_multisegments(left_multisegment, mid_multisegment),
            right_multisegment)

    assert are_multisegments_equivalent(
            result,
            subtract_multisegments(unite_multisegments(left_multisegment,
                                                       right_multisegment),
                                   subtract_multisegments(mid_multisegment,
                                                          right_multisegment)))


@given(strategies.rational_multisegments_triplets)
def test_distribution_over_intersection(multisegments_triplet
                                        : MultisegmentsTriplet) -> None:
    (left_multisegment, mid_multisegment,
     right_multisegment) = multisegments_triplet

    result = unite_multisegments(left_multisegment,
                                 intersect_multisegments(mid_multisegment,
                                                         right_multisegment))

    assert are_multisegments_equivalent(
            result,
            intersect_multisegments(unite_multisegments(left_multisegment,
                                                        mid_multisegment),
                                    unite_multisegments(left_multisegment,
                                                        right_multisegment)))


@given(strategies.multisegments_pairs)
def test_equivalents(multisegments_pair: MultisegmentsPair) -> None:
    left_multisegment, right_multisegment = multisegments_pair

    result = unite_multisegments(left_multisegment, right_multisegment)

    assert result == symmetric_subtract_multisegments(
            symmetric_subtract_multisegments(left_multisegment,
                                             right_multisegment),
            intersect_multisegments(left_multisegment, right_multisegment))


@given(strategies.multisegments_pairs)
def test_reversals(multisegments_pair: MultisegmentsPair) -> None:
    left_multisegment, right_multisegment = multisegments_pair

    result = unite_multisegments(left_multisegment, right_multisegment)

    assert are_multisegments_similar(
            result,
            unite_multisegments(reverse_multisegment(left_multisegment),
                                right_multisegment))
    assert are_multisegments_similar(
            result,
            unite_multisegments(left_multisegment,
                                reverse_multisegment(right_multisegment)))
