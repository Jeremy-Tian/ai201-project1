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

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
