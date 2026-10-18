"""Experimental root boundaries without preserving every note's self-recovery.

Keep the original group medians, member minima and strongest route per note.
Replace only the weakest-note multiplier with the existing log-support bend.
Reference memberships remain unchanged; this is not a hierarchy policy.
"""
from fractions import Fraction

from sse_multivector.fixed_reference_member_distribution import derive_boundary
from sse_multivector.fixed_reference_note_coverage import derive_boundaries as preserve


def derive_boundaries(member_scores, member_notes):
    """Use a reference-only bend among distinct notes' best relative scores.

    Normalize relative scores by their maximum to reuse the existing [0,1]
    log-support calculation; log gaps and geometric midpoints retain their
    scale. Each note contributes once regardless of its number of headings.
    Missing bends or nonpositive support retain the original multiplier.

    No outsider or semantic label selects a boundary. Scores, group medians,
    original member minima and memberships are unchanged. Newly failing
    reference notes remain accepted; report their self-recovery separately.
    """
    result = preserve(member_scores, member_notes)
    result.update(selection='minimum_no_note_bend', note_curve=None,
                  note_curve_max_ratio=None,
                  previous_multiplier=result['multiplier'],
                  previous_multiplier_ratio=result['multiplier_ratio'],
                  previous_limiting_notes=list(result['limiting_notes']))
    if not result['notes']:
        return result
    notes = sorted(result['notes'])
    ratios = [Fraction(*result['notes'][n]['ratio']) for n in notes]
    maximum = max(ratios)
    if maximum <= 0:
        return result
    curve = derive_boundary([float(r / maximum) for r in ratios], notes)
    result.update(note_curve=curve,
                  note_curve_max_ratio=[maximum.numerator, maximum.denominator])
    if curve.get('selection') != 'member_bend':
        return result
    multiplier = max(Fraction(*result['multiplier_ratio']),
                     Fraction(curve['threshold']) * maximum)
    try:
        result.update(selection='note_bend', multiplier=float(multiplier),
                      multiplier_ratio=[multiplier.numerator, multiplier.denominator],
                      limiting_notes=[])
        for group in result['groups'].values():
            if group['median'] is not None:
                group['threshold'] = float(max(Fraction(group['minimum']),
                                               multiplier * Fraction(group['median'])))
    except OverflowError as error:
        raise ValueError('derived multiplier or threshold is not representable') from error
    return result
