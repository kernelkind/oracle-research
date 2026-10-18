"""Experimental tightening by existing root-note and group-member bends.

Both calculations use accepted-reference scores with the whole source note
already excluded. Outsiders and review labels never determine a boundary.
No hierarchy policy is activated by this module.
"""
from sse_multivector.fixed_reference_member_distribution import derive_boundary
from sse_multivector.fixed_reference_note_bend import derive_boundaries as note_bend


def derive_boundaries(member_scores, member_notes):
    """Keep the stricter existing boundary, preserving unavailable groups.

    A missing group bend retains the current note-bend threshold. Existing
    accepted memberships, member statistics and root multiplier stay intact;
    references need not pass the new-outsider threshold to remain accepted.
    """
    result = note_bend(member_scores, member_notes)
    result['combination'] = 'max_note_bend_and_member_bend'
    result['note_bend_thresholds'] = {
        group: row['threshold'] for group, row in result['groups'].items()}
    result['member_bends'] = {}
    for group, row in result['groups'].items():
        local = derive_boundary(member_scores[group], member_notes[group])
        result['member_bends'][group] = local
        if row['threshold'] is not None and local['threshold'] is not None:
            row['threshold'] = max(row['threshold'], local['threshold'])
    return result
