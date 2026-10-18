"""Experimental upper-tail boundary for fixed-group title/meaning disagreement.

Use accepted groups only, with equal mass per group and no outsider or labels.
This calculation does not remove existing memberships or activate a HiGen rule.
"""
import math


def derive_boundary(group_gaps):
    """Find the strongest positive x-y bend in ascending positive gaps.

    Gaps are median cross-note title cosine minus median meaning cosine. Only
    positive gaps supply the fit; missing and nonpositive values cannot disable a
    group. Exact ties share a level. Normalize cumulative group count and gap over
    their observed endpoints, without trimming. The boundary is the arithmetic
    midpoint between the selected level and its next larger gap. Insufficient
    levels or no positive bend leave every group available. The 1e-12 tolerance
    only suppresses numerical bends on straight curves, as in the existing bends.
    """
    levels = {}
    for group, value in group_gaps.items():
        if not isinstance(group, str) or not group:
            raise ValueError('group IDs must be nonempty strings')
        if value is None:
            continue
        gap = float(value)
        if not math.isfinite(gap) or not -2 <= gap <= 2:
            raise ValueError('cosine gaps must be finite and lie in [-2,2]')
        if gap > 0:
            levels.setdefault(gap, []).append(group)
    result = dict(status='insufficient_levels', threshold=None,
                  selected_level=None, disabled_groups=[], curve=[])
    cumulative = 0
    for gap, groups in sorted(levels.items()):
        cumulative += len(groups)
        result['curve'].append(dict(gap=gap, groups=sorted(groups),
                                    cumulative_groups=cumulative))
    curve = result['curve']
    if len(curve) < 3:
        return result
    first, last = curve[0], curve[-1]
    for level in curve:
        x = ((level['cumulative_groups'] - first['cumulative_groups']) /
             (last['cumulative_groups'] - first['cumulative_groups']))
        y = (level['gap'] - first['gap']) / (last['gap'] - first['gap'])
        level.update(x=x, y=y, deviation=x-y)
    selected = max(range(1, len(curve)-1), key=lambda i: curve[i]['deviation'])
    if curve[selected]['deviation'] <= 1e-12:
        result['status'] = 'no_positive_bend'
        return result
    threshold = (curve[selected]['gap'] + curve[selected+1]['gap']) / 2
    result.update(status='boundary', threshold=threshold, selected_level=selected,
                  disabled_groups=sorted(group for gap, groups in levels.items()
                                         if gap > threshold for group in groups))
    return result
