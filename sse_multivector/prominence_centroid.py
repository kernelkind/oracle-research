"""Compare original-group mean vectors against saved title-cosine results.

No encodings or prompt calls. Uses original memberships and recorded node merges,
never expanded memberships or child masks, to construct the mean vectors.
"""
import argparse
import math
from pathlib import Path

try:
    from .prominence_cosine import read, sha, save, decode, cosine, rank_rows
except ImportError:
    from prominence_cosine import read, sha, save, decode, cosine, rank_rows


def centroid(vectors):
    if not vectors:
        raise ValueError("empty centroid")
    dimensions = len(vectors[0])
    normalized = []
    for vector in vectors:
        norm = math.sqrt(math.fsum(x*x for x in vector))
        if len(vector) != dimensions or not norm or not math.isfinite(norm):
            raise ValueError("invalid centroid member")
        normalized.append([x/norm for x in vector])
    result = [math.fsum(v[i] for v in normalized)/len(normalized) for i in range(dimensions)]
    cosine(result, result)  # Refuse a zero mean rather than invent its direction.
    return result


def compare(baseline, packets_path, canonical_path, output):
    plan = read(baseline / "plan.json")
    previous = read(baseline / "comparison.json")
    vectors_dir = Path(plan["vectors"])
    for name in ("vector-map.json", "normalized-vectors.f64le"):
        path = vectors_dir / name
        if sha(path) != plan["protected"][str(path)]:
            raise ValueError("saved vectors or mapping changed")
    mapping = read(vectors_dir / "vector-map.json")["vectors"]
    by_id = {r["short_id"]: r for r in mapping}
    vectors = decode(vectors_dir / "normalized-vectors.f64le", plan["encoder"]["model"]["dimensions"], "d")
    packets = {p["packet"]: p for p in read(packets_path)["packets"]}
    consolidations = {c["canonical"]: c["source_group_ids"] for c in read(canonical_path)["consolidations"]}
    groups, membership, ranking = {}, {}, {}
    for nid, old_rows in previous["groups"].items():
        source_ids = consolidations.get(nid, [nid])
        members, source_means, unique = [], {}, set()
        for source_id in source_ids:
            source_members = []
            for item in packets[source_id]["instances"]:
                mid = item["instance"]
                row = by_id[mid]
                if (row["vector_id"] != item["vector_id"] or row["note_id"] != item["note_id"]
                        or row["byte_spans"] != item["byte_spans"] or row["fragments"] != item["fragments"]):
                    raise ValueError(f"source packet differs from saved vector: {mid}")
                source_members.append(mid)
                key = (row["note_id"], tuple(map(tuple, row["byte_spans"])))
                if key not in unique:
                    members.append(mid)
                    unique.add(key)
            source_means[source_id] = centroid([vectors[by_id[mid]["ordinal"]] for mid in source_members])
        mean = centroid([vectors[by_id[mid]["ordinal"]] for mid in members])
        membership[nid] = dict(source_groups=source_ids, mask_ids=members,
                               posts=sorted({by_id[mid]["note_short_id"] for mid in members}))
        rows = []
        for old in old_rows:
            vector = vectors[old["ordinal"]]
            similarity = cosine(vector, mean)
            rows.append(dict(old, title_cosine=old["cosine"], title_product=old["product"],
                             cosine=similarity, is_centroid_member=bool(set(old["mask_ids"]) & set(members)),
                             original_group_cosines={sid:cosine(vector,m) for sid,m in source_means.items()}))
        groups[nid] = rows
        ranking[nid] = rank_rows(rows)
    result = dict(groups=groups, rankings=ranking, centroid_membership=membership,
                  formula="Equal-weight mean of unit original-member vectors; cosine * unchanged prominence",
                  caveat="Member-mask similarities are in-sample, not independent validation. No title-specific calibration.",
                  source_sha256={str(p.resolve()):sha(p) for p in
                      (baseline / "plan.json", baseline / "comparison.json", packets_path, canonical_path, Path(__file__))})
    save(output, result)
    print("Compared",sum(map(len,groups.values())),"masks; no inference.")
    for nid, info in membership.items():
        print(nid, len(info["mask_ids"]), "original masks,",len(info["posts"]),"posts")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("--packets", type=Path, required=True)
    p.add_argument("--canonical", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    compare(args.baseline, args.packets, args.canonical, args.output)


if __name__ == "__main__":
    main()
