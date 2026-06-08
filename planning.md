# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Off-campus housing for Stevens Institute of Technology students** in Hoboken, NJ and the
surrounding Hudson County towns (Jersey City, Weehawken, Union City).

Stevens' own pages only point students to listing sites and offer generic advice like "visit
the area during the day and at night" — they don't tell you which specific buildings nickel-and-dime
tenants, which streets and floors flood, where broker fees and mid-lease rent hikes bite hardest,
or how the Hoboken-vs-Jersey-City price tradeoff actually plays out on a student budget. That
lived-experience knowledge is scattered across building-review sites, neighborhood blogs, and
Reddit threads, so answering one concrete question (e.g. "is the Hudson Tea Building worth the rent?")
means reading across all of them — exactly the gap a retrieval system can close.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Stevens — "Living on Your Own" | Official off-campus housing guidance: safety, commuting, finding an apartment | https://www.stevens.edu/living-on-your-own |
| 2 | Stevens — Graduate Student Housing | Official off-campus + international student resources, roommate discussion board | https://www.stevens.edu/housing-resources-for-graduate-students |
| 3 | Redfin — Hoboken Neighborhood Guide | Where-to-live breakdown by area (Downtown / Uptown / Waterfront) | https://www.redfin.com/blog/hoboken-nj-neighborhoods/ |
| 4 | Apartments.com — Hoboken Local Guide | Rental price ranges by bedroom count and neighborhood | https://www.apartments.com/local-guide/hoboken-nj/ |
| 5 | NJ Real Estate Network — Moving to Hoboken | Long-form guide: cost of living, flooding risk, parking, commute | https://www.newjerseyrealestatenetwork.com/blog/moving-to-hoboken-nj/ |
| 6 | ApartmentRatings — Hoboken South Waterfront (333 River St) | 155 tenant reviews; management/fee complaints vs. amenities | https://www.apartmentratings.com/nj/hoboken/hoboken-south-waterfront_201222100007030/ |
| 7 | ApartmentRatings — Hudson Tea Building (1500 Washington St) | 61 tenant reviews; recurring flooding/maintenance issues | https://www.apartmentratings.com/nj/hoboken/the-hudson-tea-building_201792890007030/ |
| 8 | ApartmentRatings — 101 Clinton Street | 14 tenant reviews; strict-but-well-run, lower comparable rent | https://www.apartmentratings.com/nj/hoboken/101-clinton-street_201659900707030/ |
| 9 | ApartmentRatings — Hoboken (sorted by reviews) | Aggregate page across ~50 buildings; cross-building comparison | https://www.apartmentratings.com/nj/hoboken/sort-by-reviews/ |
| 10 | Renters Canary — Hoboken | Tenant reviews on rent hikes and landlord behavior across addresses | https://www.renterscanary.com/city/Hoboken |
| 11 | Quora — Cost of living for a student in Hoboken / JC / Union City | Student-perspective Q&A comparing the three towns | https://www.quora.com/What-is-the-cost-of-living-for-a-student-in-Hoboken-Jersey-City-or-Union-City-NJ |
| 12 | r/Hoboken | Community threads on neighborhoods, broker fees, landlords, "where to live" | https://www.reddit.com/r/Hoboken/ |
| 13 | r/Stevens | Student threads on off-campus apartments and roommates near campus | https://www.reddit.com/r/Stevens/ |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
