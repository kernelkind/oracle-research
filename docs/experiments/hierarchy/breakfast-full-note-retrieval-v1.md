# Breakfast meaning compared with every full post

The user requested a direct SSE comparison between the entire saved Breakfast
meaning and every entire original post in the fifty-note construction. No
heading/meaning mixtures, learned scoring or graph features were applied.

**Historical investigation:** the query meaning derives from deprecated ASv6.48
subjects. This is not current-ASv6.100 pipeline validation. Raw original posts
are unchanged and are not deprecated by the subject-version rule.

## Method

- Select Breakfast's exact saved meaning from construction step 81. Encode that
  string by itself, selecting its full UTF-8 byte span for SSE pooling.
- Select all fifty distinct note IDs processed in the saved construction.
  Include the incoming Breakfast note. Encode each complete original post,
  selecting its full byte span, including links, mentions, tags and emoji.
- Use the existing native SSE worker, pinned checkpoint, sentence-T5-base model,
  selected-token pooling and 768 dimensions. These are whole-text auxiliary
  representations; they are not new MP-selected masks.
- Rank the fifty post vectors by cosine against the meaning vector. Annotate
  existing canonical nodes whose direct supporting entries belong to each post;
  do not aggregate their scores or select canonical comparisons.

The worker produced all 51 vectors. Every non-special token was pooled; the
longest input had 258 tokens, below the 512-token limit. There was no truncation.
The regenerated query vector matches the previous standalone full-meaning vector
at cosine 1.0, with identical checkpoint, model, pooling and dimension identities.
Source text, request and output hashes are retained. No teacher/provider calls,
prompt edits, hierarchy changes or UI refresh occurred.

## Results

Descriptions below identify posts; they are not new node headings.

| Post rank | Cosine | Post description | Relevant existing canonical support |
|---:|---:|---|---|
| 1 | 0.516358 | Late breakfast after a morning gym session | Greetings C027 |
| 2 | 0.512756 | A Chinese takeout worker eating a dish absent from the menu | Restaurants C023 |
| 3 | 0.496948 | Leftover chicken pizza and shrimp tempura sushi for dinner | Meals C013 |
| 4 | 0.486329 | Packing a lunch box with the right amount of food | Lunch preparation C014 |
| 5 | 0.468307 | Intention to start meal planning | Meal planning C009 |
| 6 | 0.459637 | Dinner of bread, butter, avocado and eggs | Meals C015 |
| 11 | 0.398691 | The incoming local-breakfast post at Roti IKHWANA | Incoming note |
| 12 | 0.371738 | Making pancakes in response to a child's request | Making pancakes C069 |
| 13 | 0.344062 | Growing food and frying homegrown tomatoes for breakfast | Homegrown food C071 |

Both posts supporting the Meals candidates appear in the first six. The
Homegrown food and pancake-making posts appear later. This is useful evidence
for the proposed retrieval direction in this one case. These are **post ranks**,
not canonical-node ranks; they are not directly the same metric as the earlier
canonical shortlist positions. A relevant post can support several unrelated
headings, and its score alone does not decide which canonical nodes to compare.
The incoming note ranking eleventh is also retained rather than filtered away.

The next discussion should examine how matching posts would nominate their
associated canonical nodes, before choosing a cutoff or changing construction.
One query does not establish whole-hierarchy quality or API-cost savings.

## Reproduction and evidence

[Preparation and ranking](../../../sse_multivector/full_text_retrieval.py) use the production SSE request
parser and receipt/vector reader. Three new tests cover full UTF-8 spans,
construction-note membership, source-change refusal, self-match retention and
request-binding refusal. All 27 related unit/worker tests passed, followed by
the actual 51-vector native worker run and ranking.

Ignored evidence is retained under
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1/target/breakfast-full-note-retrieval-v1/`:
`inputs.json`, `worker-request.json`, `worker-config.json`, `worker-result/`,
`ranking.json` and `data-status.json`. The ranking contains all fifty scores and
complete original posts.  Production selection is unchanged.
