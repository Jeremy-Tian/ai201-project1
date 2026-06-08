# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**Off-campus housing for Stevens Institute of Technology students** in Hoboken, NJ and the
surrounding Hudson County towns (Jersey City, Weehawken, Union City).

Stevens' own pages only point students to listing sites and offer generic advice like "visit
the area during the day and at night" — they don't tell you which specific buildings nickel-and-dime
tenants, which streets and floors flood, where broker fees and mid-lease rent hikes bite hardest,
or how the Hoboken-vs-Jersey-City price tradeoff actually plays out on a student budget. That
lived-experience knowledge is scattered across building-review sites, neighborhood blogs, and
Reddit threads, so answering one concrete question means reading across all of them — exactly the
gap a retrieval system can close.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Stevens — "Living on Your Own" | Official guide | https://www.stevens.edu/living-on-your-own |
| 2 | Stevens — Graduate Student Housing | Official guide | https://www.stevens.edu/housing-resources-for-graduate-students |
| 3 | Redfin — Hoboken Neighborhood Guide | Neighborhood guide | https://www.redfin.com/blog/hoboken-nj-neighborhoods/ |
| 4 | Apartments.com — Hoboken Local Guide | Price/neighborhood guide | https://www.apartments.com/local-guide/hoboken-nj/ |
| 5 | NJ Real Estate Network — Moving to Hoboken | Long-form guide | https://www.newjerseyrealestatenetwork.com/blog/moving-to-hoboken-nj/ |
| 6 | ApartmentRatings — Hoboken South Waterfront (333 River St) | Building reviews | https://www.apartmentratings.com/nj/hoboken/hoboken-south-waterfront_201222100007030/ |
| 7 | ApartmentRatings — Hudson Tea Building (1500 Washington St) | Building reviews | https://www.apartmentratings.com/nj/hoboken/the-hudson-tea-building_201792890007030/ |
| 8 | ApartmentRatings — 101 Clinton Street | Building reviews | https://www.apartmentratings.com/nj/hoboken/101-clinton-street_201659900707030/ |
| 9 | ApartmentRatings — Hoboken (sorted by reviews) | Review aggregator | https://www.apartmentratings.com/nj/hoboken/sort-by-reviews/ |
| 10 | Renters Canary — Hoboken | Tenant reviews | https://www.renterscanary.com/city/Hoboken |
| 11 | Quora — Cost of living for a student in Hoboken / JC / Union City | Q&A / student perspective | https://www.quora.com/What-is-the-cost-of-living-for-a-student-in-Hoboken-Jersey-City-or-Union-City-NJ |
| 12 | r/Hoboken | Community forum | https://www.reddit.com/r/Hoboken/ |
| 13 | r/Stevens | Community forum | https://www.reddit.com/r/Stevens/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 600 characters (≈140 tokens)

**Overlap:** 100 characters, applied when a single paragraph must be windowed

**Why these choices fit your documents:** The corpus mixes short tenant reviews with longer
guides. The chunker (`ingest.py`) is paragraph-aware: it packs whole blocks up to 600 chars so a
single review stays intact as one chunk, splits long guide paragraphs with a 100-char overlap to
preserve boundary-straddling facts, and merges bare section headers into the section they
introduce. 600 chars keeps every chunk under `all-MiniLM-L6-v2`'s 256-token truncation limit.
Preprocessing strips HTML tags, decodes entities, removes web boilerplate, and prepends each chunk
with its source label for attribution.

**Final chunk count:** 51 chunks across 13 documents (avg ~424 chars, max 157 tokens). *(Sample
corpus — recount after replacing the sample documents with real collected sources.)*

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, runs locally, free, no
API key). Embeddings are normalized and stored in ChromaDB with cosine distance, so a score of 0
means identical and ~1 means unrelated. Each chunk is embedded with its source label prepended;
the clean text is stored for display and attribution. Retrieval defaults to top-k=5 with an
optional cosine-distance threshold to drop weak matches.

**Production tradeoff reflection:** If cost weren't a constraint, I'd weigh a stronger hosted
embedder (OpenAI `text-embedding-3-large`, Voyage `voyage-3`, which Anthropic recommends for
retrieval). The gains: better domain accuracy (distinguishing near-duplicate housing language and
recognizing that "333 River St" *is* "Hoboken South Waterfront"), longer context windows so whole
reviews embed without splitting, and multilingual support for Stevens' many international students
(e.g. Cohere `embed-multilingual-v3`). The costs: per-call latency, API spend, and sending
document text to a third party. For this project the local MiniLM wins on simplicity, privacy, and
zero cost; at scale I'd benchmark a hosted model's accuracy gain against its cost-per-query before
switching.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The system prompt (`query.py`) tells the model to answer
*only* from the numbered context passages, forbids outside/general knowledge, and requires it to
reply with exactly "I don't have enough information on that in the documents I have." when the
context is insufficient — no guessing or padding with general advice. It also instructs the model
to cite source filenames inline and to attribute conflicting opinions ("some reviewers say…")
rather than stating them as fact. Temperature is set to 0.1 to keep output close to the source
text.

Grounding is enforced structurally, not just by instruction:
- Retrieval applies a cosine-distance threshold (0.65). If no chunk clears it, `ask()` returns the
  refusal **without ever calling the LLM**, so an off-topic question can't be answered from
  training knowledge.
- The context block numbers each chunk and tags it with its source filename, so the model has an
  explicit handle to cite.

**How source attribution is surfaced in the response:** Sources are built **programmatically** from
the retrieved chunks' metadata (unique source filenames, in order of first appearance) and returned
in the result — they are not parsed out of the model's text, so attribution holds even if the model
forgets to cite. When the answer is the refusal, the source list is suppressed so it never implies
the answer came from documents it didn't use. The Gradio UI (`app.py`) shows the answer and the
"Retrieved from" source list in separate boxes.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do tenants say about flooding at the Hudson Tea Building? | Recurring bathroom flooding reported (~4–5×/week for ~5 months) before it was fixed. | Reports the 4–5×/week flooding from one tenant, **correctly notes it isn't mentioned as building-wide**, and separates it from general Hoboken flooding. Cited Hudson Tea + Reddit. | Relevant (top hit 0.262; tail 0.53–0.59) | Accurate |
| 2 | How should I pick an apartment in Hoboken to minimize flood risk? | Avoid basement/first-floor units; Hoboken is low-lying and floods; higher floors safer. | "Avoid basement and first-floor apartments… higher floors are safer." Cited NJ guide + Reddit. | Relevant (top hit 0.259) | Accurate |
| 3 | Is Uptown or Downtown Hoboken quieter and cheaper? | Uptown is quieter/more residential and somewhat cheaper (~$3,852 1-BR); Downtown is pricier with more nightlife/PATH access. | Uptown quieter and cheaper, ~$3,852 one-bedroom, makes sense for a grad student. Cited Redfin + NJ guide + Reddit. | Relevant (top hits 0.231 / 0.243) | Accurate |
| 4 | For a student on a budget, how does Jersey City compare to Hoboken? | Hoboken is priciest; JC cheaper overall (though downtown JC waterfront has caught up); the Heights saves the most. | JC "a notch cheaper," downtown JC waterfront "caught up," Heights is where you "actually save money." Cited Quora. | Relevant (top hit 0.212) | Accurate |
| 5 | What are tenants' complaints about management at 333 River Street? | Nickel-and-diming (kitchen-light charge, repeated renters-insurance requests) and a steep non-negotiable renewal increase, despite good amenities. | Reports nickel-and-diming, renters-insurance hassle, and the renewal increase — all from the 333 River reviews. | **Partially relevant** — correct chunk at rank 1 (0.311), but a wrong-building 101 Clinton chunk at rank 2 (0.371); see Failure Case Analysis. | Accurate (answer cited only 333 River) |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

**Out-of-domain check:** "What's the best pizza in Hoboken?" correctly returns the refusal message with no sources — confirming the system declines rather than answering from training knowledge.

> Note: the current corpus is synthetic `SAMPLE` test data, so these answers reflect the sample
> text, not verified real-world Hoboken facts. The pipeline behavior (retrieval quality, grounding,
> attribution) is what this report evaluates.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "What are tenants' complaints about management at Hoboken South
Waterfront (333 River Street)?" — specifically the *retrieval and attribution*, not the final
answer text.

**What the system returned:** The generated answer was correct and cited only
`apartmentratings_333_river_hoboken_south_waterfront.txt`. But the retriever's top-5 included a
**101 Clinton Street** chunk at rank 2 (cosine distance 0.371) and another at rank 4 — a different
building entirely. Because source attribution is built from *all retrieved chunks*, the UI's
"Retrieved from" box listed `333_river`, `101_clinton`, and `maxwell_place`, so two of the three
displayed sources contributed nothing to the answer.

**Root cause (tied to a specific pipeline stage):** Two stages combine:
1. **Embedding/retrieval.** `all-MiniLM-L6-v2` encodes the *topic* ("management complaints, rent,
   maintenance") much more strongly than the *building identity*. The phrase "Hoboken South
   Waterfront / 333 River Street" doesn't pull hard enough to exclude other buildings' management
   reviews, so a 101 Clinton management chunk lands at rank 2. This is the building-name vs.
   address ambiguity anticipated in planning.md (challenge #4).
2. **Attribution design.** `ask()` lists every retrieved source rather than only the sources the
   model actually cited, so retrieval's false positives leak into the displayed attribution.

**What you would change to fix it:** (a) Filter attribution to the sources the model cited inline
(parse the `(source: …)` tags and intersect with retrieved metadata) so the "Retrieved from" list
reflects what was used, not just what was fetched; (b) tighten the relevance threshold or add a
light re-rank that boosts chunks whose source/text contains the building name from the query; and
(c) at ingestion, prepend each chunk with both the building name *and* street address so a query
phrased either way retrieves the right building more decisively.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the Chunking Strategy and Retrieval
Approach sections in planning.md *before* coding meant the implementation had concrete targets
instead of guesses. Because I had already reasoned that `all-MiniLM-L6-v2` truncates at 256 tokens
and that my corpus mixes short reviews with long guides, the chunker was built around those
constraints from the start (600-char chunks that keep most reviews whole), and the `--check-tokens`
verification confirmed no chunk exceeded the limit. The pipeline diagram also made the module
boundaries obvious — ingest → chunk → embed → retrieve → generate became one file per stage.

**One way your implementation diverged from the spec, and why:** The spec described chunking as
"600-char chunks with 100-char overlap," which reads like a fixed-width sliding window. In
implementation I diverged to a **paragraph-aware** chunker: it packs whole review/paragraph blocks
up to 600 chars and only applies the overlap when it must split a paragraph longer than that. I
made this change after inspecting the first chunk output — a blind window was splitting individual
tenant reviews mid-opinion and orphaning section headers (e.g. a bare "Flooding" heading at the end
of a chunk). The paragraph-aware approach honored the spec's actual *intent* ("one review = one
coherent chunk") better than its literal wording, so I updated planning.md to record the change and
why.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Ingestion + chunking code**

- *What I gave the AI:* My Chunking Strategy section and pipeline diagram from planning.md (600-char
  chunks, 100-char overlap, source-label prepend, HTML/whitespace cleaning), plus a sample short
  review file and a sample long guide file.
- *What it produced:* A `load → clean → chunk → inspect` script (`ingest.py`) with a character-based
  chunker and an inspection report printing chunk counts and sample chunks.
- *What I changed or overrode:* After running the inspection step, I saw the chunker was orphaning a
  bare "Flooding" section header at the end of a chunk and could split reviews mid-opinion, so I
  directed it to make the chunker **paragraph-aware** and to **merge headers forward** into their
  section. I also caught a NumPy 2.x/torch ABI crash during the token check and pinned `numpy<2` in
  requirements.txt rather than accepting the broken environment.

**Instance 2 — Embedding, retrieval, and grounded generation**

- *What I gave the AI:* My Retrieval Approach and Grounded Generation requirements (all-MiniLM-L6-v2,
  ChromaDB with source metadata, top-k=5, answers from context only with source attribution).
- *What it produced:* `retrieval.py` (embed + ChromaDB + `retrieve()`) and `query.py` (`ask()` with a
  grounding system prompt + Groq call), plus the Gradio UI.
- *What I changed or overrode:* I directed two things the first pass didn't do well. (1) I had it
  configure ChromaDB with **cosine** distance instead of the default L2 so the scores matched the
  0.6–0.7 thresholds I use for debugging. (2) I made grounding **structural, not just prompted**: if
  no chunk clears the relevance threshold, `ask()` returns the refusal *without calling the LLM*, and
  the source list is built programmatically from metadata (and suppressed on refusal) rather than
  trusting the model to cite. I verified this with an out-of-domain question ("best pizza in
  Hoboken?") that correctly refused.
