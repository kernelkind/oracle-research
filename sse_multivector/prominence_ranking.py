"""Offline ranking sensitivity comparison; no fitted calibration or inference."""

import copy
import math


VARIANTS = ("Prominence", "Linear cosine")
INVERSE_VARIANTS = ("Inverse combined", "Full-post cosine")


def cosine_weight(value):
    if (type(value) not in (float, int) or not math.isfinite(value)
            or not -1.000001 <= value <= 1.000001):
        raise ValueError("invalid cosine")
    return (max(-1, min(1, value)) + 1) / 2


def ranking_scores(row):
    """One calculation shared by saved comparisons and the review UI."""
    prominence = row['prominence']
    if type(prominence) is not int or not 0 <= prominence <= 100:
        raise ValueError('invalid prominence')
    result = dict(linear_product=prominence * cosine_weight(row['cosine']))
    if 'inverse_cosine' in row or 'full_post_cosine' in row:
        if 'inverse_cosine' not in row or 'full_post_cosine' not in row:
            raise ValueError('incomplete inverse comparison')
        inverse = row['inverse_cosine']
        if inverse is None:
            if prominence != 100:
                raise ValueError('empty inverse cannot account for missing meaning')
            contribution = 0
        else:
            contribution = (100 - prominence) * cosine_weight(inverse)
        result.update(inverse_product=result['linear_product'] + contribution,
                      full_post_score=100 * cosine_weight(row['full_post_cosine']))
    return result


def add_rankings(batch, report, comparison):
    """Join saved similarities by exact case identity, then add viewer orderings."""
    saved = {}
    for node_id, rows in comparison["groups"].items():
        for row in rows:
            if row["id"] in saved or row["node_id"] != node_id:
                raise ValueError("duplicate or misplaced cosine case")
            saved[row["id"]] = row
    result = copy.deepcopy(batch)
    cards = {n["id"]: n for n in result["notes"]}
    inverse = any('inverse_cosine' in saved.get(c['id'], {})
                  or 'full_post_cosine' in saved.get(c['id'], {}) for c in report['cases'])
    variants = VARIANTS + INVERSE_VARIANTS if inverse else VARIANTS
    groups, values = {}, {}
    for case in report["cases"]:
        cid, evidence = case["id"], case["evidence"]
        groups.setdefault(evidence["node_id"], []).append(cid)
        values[cid] = None
        if case["status"] != "valid":
            continue  # Keep unscored cards after scored cards in every order.
        row = saved.get(cid)
        fragments = [evidence["text"].encode()[a:b].decode()
                     for a, b in evidence["byte_spans"]]
        expected = dict(node_id=evidence["node_id"], title=evidence["node_title"],
                        note_id=evidence["note_id"], mask_ids=evidence["mask_ids"],
                        fragments=fragments, prominence=case["parsed"]["prominence"])
        if row is None or any(row.get(k) != v for k, v in expected.items()):
            raise ValueError(f"missing or stale cosine case: {cid}")
        cosine = row.get("cosine")
        scores = ranking_scores(row)
        values[cid] = [expected["prominence"], scores['linear_product']]
        if inverse:
            if 'inverse_product' not in scores:
                raise ValueError(f'incomplete inverse comparison: {cid}')
            values[cid].extend([scores['inverse_product'], scores['full_post_score']])
        card = cards[cid]
        card["title"] = (f"{evidence['node_title']} [{evidence['node_id']}] · "
                         f"{evidence['note_id']} · {', '.join(evidence['mask_ids'])}")
        card["results"][0]["output"] = (
            f"Prominence: {expected['prominence']} / 100\nCosine: {cosine:.4f}\n"
        )
        if inverse:
            label = 'empty' if row['inverse_cosine'] is None else f"{row['inverse_cosine']:.4f}"
            card['results'][0]['output'] += (
                f"Inverse cosine: {label}\nFull-post cosine: {row['full_post_cosine']:.4f}\n")
    result["orderings"] = []
    for index, name in enumerate(variants):
        ordering = []
        for ids in groups.values():
            ranked = sorted(ids, key=lambda cid: (
                values[cid] is None, -values[cid][index] if values[cid] else 0, cid))
            ordering.extend(ranked)
            valid = [cid for cid in ranked if values[cid] is not None]
            # Competition ranks preserve genuine ties; IDs only stabilize browsing.
            last_score, rank = None, 0
            for position, cid in enumerate(valid, 1):
                score = values[cid][index]
                if score != last_score:
                    rank = position
                last_score = score
                cards[cid]["results"][0]["output"] += (
                    f"\n{name}: {score:.2f} · rank {rank}/{len(valid)}"
                )
        result["orderings"].append(dict(name=name, note_ids=ordering))
    for card in result["notes"]:
        card["results"][0]["comment"] += (
            "\n\nRanking diagnostic, not calibrated relevance. "
            "Linear cosine score = prominence × (cosine + 1) / 2. "
            "Cosine's native range −1..1 maps to weight 0..1; this is not a probability. "
            "Equal scores are tied; case IDs stabilize order. "
            "Press s to change ordering at the same position (the post may change). "
            "Memberships and model outputs are unchanged. No post-score aggregation."
        )
        if inverse:
            card['results'][0]['comment'] += (
                '\nInverse combined = Linear cosine + (100 − prominence) × '
                '(inverse cosine + 1) / 2. Full-post cosine = 100 × (full-post cosine + 1) / 2. '
                'Inverse spans and full-post spans are encoded in the unchanged complete post. '
                'These scores are not percentages of meaning.')
    result["title"] = "Prominence × rescaled cosine · saved-score comparison"
    return result
