# Mechanical assembly of explicit, separately recorded assistant judgments.
# Usage: jq --slurpfile decisions <combined-decision-array.json> -f THIS review.json
($decisions[0] | map(.notes | keys[]) | length) as $reviewed_notes |
if $reviewed_notes != (.notes | length) then error("review coverage differs") else . end |
{
  schema_version: 1,
  reviewer: "primary assistant and two named independent assistant reviewers",
  source_review: "subjects-review/review.json",
  review_documents: $decisions[0],
  notes: (.notes | to_entries | map(
    . as $entry |
    (($entry.key+1)|tostring) as $number |
    [$decisions[0][] | select(.notes[$number] != null)] as $owners |
    if ($owners|length) != 1 then error("missing/duplicate note review") else . end |
    $owners[0] as $owner | $owner.notes[$number] as $decision |
    $entry.value.outputs[0] as $output |
    $output.parsed_response.subjects as $subjects |
    if ($entry.value.outputs|length) != 1 or $output.status != "succeeded" or
       ($subjects|length) != $decision.reviewed_subject_count
    then error("subject receipt/count differs from explicit review") else . end |
    ($entry.value | del(.outputs)) + {
      subjects: ($subjects | to_entries | map(
        . as $s | (($s.key+1)|tostring) as $index |
        ($decision.corrections[$index] // null) as $correction |
        {
          id: ($output.call_id | sub("-AS$";"-S")) + ("000"+$index)[-3:],
          context: $s.value.context,
          subject: ($correction.subject // $s.value.subject),
          judgment: (if $decision.rejected[$index] != null then "rejected"
                     elif $decision.unresolved[$index] != null then "unresolved"
                     else "accepted" end),
          provenance: {
            call_id: $output.call_id,
            raw_subject_index: $s.key,
            raw_subject: $s.value.subject,
            run_manifest_sha256: $output.run_manifest_sha256,
            results_sha256: $output.results_sha256,
            correction: $correction,
            subject_review: {reviewer:$owner.reviewer,reason:$decision.reason}
          }
        }
      ))
    }
  ))
}
