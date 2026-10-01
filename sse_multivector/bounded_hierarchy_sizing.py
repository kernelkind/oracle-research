"""Offline, frozen-evidence capacity certificates for the BCPv5 packer.

This bounds rendered o200k input tokens, not provider usage, output, or billing.
No inference is performed. A certificate must be recalculated when evidence,
the eligible pair universe, the template, or packing limits change.
"""

import hashlib
import re

try:
    from .bounded_hierarchy_workflow import compact, MAX_PAIRS, MAX_INPUT_TOKENS
    from .experiment_inputs import render
except ImportError:
    from bounded_hierarchy_workflow import compact, MAX_PAIRS, MAX_INPUT_TOKENS
    from experiment_inputs import render


def comparison_capacity_bound(nodes, template, candidate_pairs):
    """Certify a minimum occupancy for every nonfinal greedy comparison batch.

    ``candidate_pairs`` is the actual bounded eligible universe, not all node
    combinations. Each pair is canonicalized like comparison preparation.
    Evidence uses the production compact JSON representation unchanged.

    Interior o200k pre-token pieces cannot be affected by joining JSON objects:
    their first and last pieces are punctuation runs. The finite joins below
    are tokenized separately, retaining their worst exact token-count deltas.
    The sum of the largest 2*k eligible node costs consequently covers any k
    pairs, including pairs sharing no evidence. Fail closed if this lexical
    invariant is not present. Capacity zero means the conservative certificate
    cannot guarantee even one pair; it does not assert every pair is oversized.
    """
    import regex
    import tiktoken

    if not isinstance(nodes, dict) or any(not isinstance(v, list) or not 1 <= len(v) <= 2
                                          for v in nodes.values()):
        raise ValueError("node evidence requires one or two compact original entries")
    if sum(map(len, nodes.values())) > 5000:
        raise ValueError("offline capacity source exceeds 5000 evidence entries")
    if not isinstance(template, str) or template.count("{INPUT_JSON}") != 1:
        raise ValueError("capacity proof requires exactly one INPUT_JSON placeholder")
    # Use production placeholder validation, rather than a separate renderer.
    render(template, dict(INPUT_JSON=""))
    pairs, eligible = set(), set()
    for position, pair in enumerate(candidate_pairs, 1):
        if position > 100000:
            raise ValueError("offline capacity universe exceeds 100000 supplied pairs")
        if (not isinstance(pair, (tuple, list)) or len(pair) != 2
                or any(not isinstance(n, str) or not re.fullmatch(r"S\d{4}", n)
                       or n not in nodes for n in pair) or pair[0] == pair[1]):
            raise ValueError("eligible comparison pairs require two distinct saved S#### IDs")
        a, b = sorted(pair)
        pairs.add((a, b))
        eligible.update((a, b))

    encoding = tiktoken.get_encoding("o200k_base")
    pattern = regex.compile(encoding._pat_str)
    count = lambda value: len(encoding.encode(value))

    def pieces(value):
        result = pattern.findall(value)
        if not result or "".join(result) != value:
            raise ValueError("tokenizer pre-token partition cannot be certified")
        return result

    def boundary(value):
        # At least two nonspace punctuation characters prevent the optional
        # one-character prefix of a word piece from reaching an interior word.
        if (regex.search(r"[\p{L}\p{N}\p{M}]", value)
                or len(regex.sub(r"\s", "", value)) < 2):
            raise ValueError("JSON punctuation boundary cannot be certified")
        return value

    def ends(value):
        p = pieces(value)
        if len(p) < 3:
            raise ValueError("JSON object interior cannot be certified")
        return boundary(p[0]), boundary(p[-1])

    def delta(left, right, joiner=""):
        # Both old boundary pieces are removed; their combined replacement is
        # the only part of the tokenization that can change at this seam.
        joined = left + joiner + right
        if any(regex.search(r"[\p{L}\p{N}\p{M}]", p) for p in pieces(joined)):
            raise ValueError("joined punctuation boundary cannot be certified")
        return count(joined) - count(left) - count(right)

    serialized_nodes = {n: compact(dict(id=n, entries=nodes[n])) for n in sorted(eligible)}
    serialized_pairs = [compact(dict(id=a + "-" + b, A=a, B=b))
                        for a, b in sorted(pairs)]
    digest = lambda value: hashlib.sha256(compact(value).encode("utf-8")).hexdigest()
    proof = dict(tokenizer="o200k_base", eligible_nodes=len(eligible), candidate_pairs=len(pairs),
                 evidence_entries=sum(len(nodes[n]) for n in eligible),
                 template_sha256=hashlib.sha256(template.encode("utf-8")).hexdigest(),
                 nodes_sha256=digest(serialized_nodes), candidate_pairs_sha256=digest(sorted(pairs)),
                 max_pairs=MAX_PAIRS, max_input_tokens=MAX_INPUT_TOKENS)
    if not pairs:
        return dict(guaranteed_pairs_per_request=MAX_PAIRS,
                    max_rendered_tokens_bound=0, proof=dict(proof, empty_universe=True))

    prefix, suffix = template.split("{INPUT_JSON}")
    head, middle, tail = prefix + '{"nodes":[', '],"pairs":[', ']}' + suffix
    head_end = boundary(pieces(head)[-1])
    middle_first, middle_last = ends(middle)
    tail_first = boundary(pieces(tail)[0])
    node_ends = {ends(s) for s in serialized_nodes.values()}
    pair_ends = {ends(s) for s in serialized_pairs}
    # Production JSON field ordering makes these singleton sets. Keeping this
    # explicit prevents a future serializer change from invalidating the bound.
    node_first = {first for first, _ in node_ends}
    pair_first = {first for first, _ in pair_ends}
    pair_last = {last for _, last in pair_ends}
    if len(node_first) != 1 or len(pair_first) != 1 or len(pair_last) != 1:
        raise ValueError("production JSON boundary shape cannot be certified")
    nf, pf, pl = next(iter(node_first)), next(iter(pair_first)), next(iter(pair_last))
    node_last = {last for _, last in node_ends}
    seams = dict(head_node=delta(head_end, nf),
                 node_node=max(delta(last, nf, ",") for last in node_last),
                 node_middle=max(delta(last, middle_first) for last in node_last),
                 middle_pair=delta(middle_last, pf), pair_pair=delta(pl, pf, ","),
                 pair_tail=delta(pl, tail_first))
    node_costs = sorted((count(s) for s in serialized_nodes.values()), reverse=True)
    max_pair_cost = max(map(count, serialized_pairs))
    constant_cost = sum(map(count, (head, middle, tail)))
    capacities = []
    for k in range(1, MAX_PAIRS + 1):
        # Fewer distinct nodes can remove negative node-node seam deltas, so
        # positive deltas use the maximum count and negative ones use minimum.
        max_nodes = min(2 * k, len(node_costs))
        node_seams = ((max_nodes - 1) if seams["node_node"] >= 0 else 1)
        boundary_cost = (seams["head_node"] + node_seams * seams["node_node"]
                         + seams["node_middle"] + seams["middle_pair"]
                         + (k - 1) * seams["pair_pair"] + seams["pair_tail"])
        node_cost = sum(node_costs[:max_nodes])
        capacities.append(dict(pairs=k, max_distinct_nodes=max_nodes,
            node_tokens=node_cost, pair_tokens=k * max_pair_cost,
            constant_tokens=constant_cost, boundary_tokens=boundary_cost,
            rendered_tokens_upper=node_cost + k * max_pair_cost + constant_cost + boundary_cost))
    fitting = [c for c in capacities if c["rendered_tokens_upper"] <= MAX_INPUT_TOKENS]
    chosen = fitting[-1] if fitting else capacities[0]
    proof.update(constant_tokens=constant_cost, max_pair_record_tokens=max_pair_cost,
                 max_node_record_tokens=max(node_costs), seam_token_deltas=seams,
                 capacities=capacities)
    return dict(guaranteed_pairs_per_request=chosen["pairs"] if fitting else 0,
                max_rendered_tokens_bound=chosen["rendered_tokens_upper"], proof=proof)
