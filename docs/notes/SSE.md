TO AGENTS: YOU MUST NOT EDIT OR REMOVE THIS FILE

# SSE

This doc will detail from a high level how SSE was trained. We must understand this, so we can have a guage for it's strengths and weaknesses wrt our content discovery hierarchy we are building.

1. There was a dataset of 2.5 million pairs of sentences from related news articles, usually describing the same event but from different angles.
2. Each sentence was split into factual propositions
    1. GPT 3.5 acted on 25K of the pairs of sentences. It was prompted (basically): "Identify the claims and split them as much as possible without adding information"
    3. A NLI (specialized NN for figuring out entailment between statements) compares entailment for statements A and B where A is a claim from sentence 1 (in the pair) and B is a claim from sentence 2 (in the pair)
    2. Each claim generated was mechanically compared to the original sentence, and the set of matched words were used as the mask for that claim
    3. SSE Training:
       - for each pair of sentences, SSE received:
           - both complete original sentences
           - the masks corresponding to each claim, for each claim
           - a label saying which pair of claims expressed equivalent information
        - For each pair of sentences which had at least one pair of claims which expressed equivalent information (entailed):
            - for the pair(s) of claims which entailed, the weights of the SSE model were updated so when those claims were encoded again, their vectors would point in MORE similar directions (higher cosine similarity)
            - for the pair(s) of claims which DIDN'T entail, th eweights of the SSE model were updated so when those claims were encoded again, their vectors would point in LESS similar directions (lower cosine similarity)
