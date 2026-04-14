# Graph Storage Recommendation for Multi-Source Researcher Identity

## Decision

Use **Postgres as the system of record** for researcher identity, with **JSONL raw staging** and **relational edge tables** for canonical links and provenance. Do **not** start with Neo4j or Memgraph for this pipeline.

If a dedicated graph engine becomes necessary later, choose **Neo4j** by default. Memgraph is viable for low-latency, in-memory traversal workloads, but it is not the best first choice for this repo’s current shape.

## Why This Is The Right Default

This problem is mostly **identity resolution with evidence management**, not graph analytics. The hard part is not traversing a graph; it is deciding when two partial, conflicting source records should or should not collapse into one person.

For that workload, the best fit is:

- append-only raw observations
- deterministic canonicalization
- explicit merge decisions
- durable provenance on every fact
- simple operational footprint

That is a relational problem first. A graph engine only becomes justified when multi-hop traversal is itself the primary workload.

In practice, teams solving this class of problem usually start with a **relational core plus immutable source observations**, then add a graph layer only if path traversal, neighborhood expansion, or analyst exploration becomes dominant. That is my inference from the storage semantics and operational tradeoffs of the systems below, not a market survey.

## Comparison

| Option | Best fit | Main tradeoff | Verdict |
|---|---|---|---|
| Neo4j | Mature property graph with strong traversal and relationship modeling | Separate graph engine, graph-specific ops, and merge discipline required | Best graph DB if we later need one |
| Memgraph | Real-time, in-memory graph traversal with Cypher and streaming connectors | Memory-centric operations and a narrower default ecosystem | Good for specialized low-latency graph workloads |
| Postgres + relational edge tables | Canonical identity store, provenance, auditability, and simple ops | Less natural for deep ad hoc traversals than a graph engine | Best fit now |
| Document store + edge table | Raw source payloads and flexible ingest | Conflicts, merges, and referential integrity become application-managed | Useful for staging, not as the canonical store |

## Write Path And Merge Semantics

The write path should treat every scraped record as an **observation**, not as truth:

1. Ingest the source payload.
2. Store the raw record and its fetch metadata.
3. Extract evidence rows for names, emails, URLs, affiliations, and papers.
4. Resolve a candidate canonical person.
5. Upsert only the canonical link rows.
6. Keep conflicting claims as separate evidence, not overwritten values.

This matters because merge semantics are where identity systems usually fail. A person node should not be the only place where a value exists. If a source says one email and another source says a different email, both claims should survive as provenance-bearing evidence until the resolver decides which one is canonical.

Neo4j can model this, but `MERGE` is not a free correctness guarantee under concurrency; Neo4j’s own docs require uniqueness constraints to make node identity safe. Memgraph can also model the same pattern, but it still leaves you with a separate graph engine and in-memory operational planning.

## When A Graph DB Is Justified

Use a graph database only if one or more of these become true:

- multi-hop traversal is on the hot path
- analysts need frequent neighborhood expansion over people, papers, affiliations, and contact paths
- path scoring or graph algorithms become part of the core product
- the graph is large enough that relational joins become the bottleneck in practice

If those conditions are not true, the graph engine is extra surface area without enough payoff.

## When Postgres Is Enough

Postgres is enough when the main jobs are:

- conservative entity resolution
- immutable provenance storage
- export and review workflows
- bounded hop queries
- audit-friendly merge history

Postgres already gives us `jsonb`, foreign keys, and atomic `ON CONFLICT` upserts, which are exactly the primitives this pipeline needs. If we want graph-style querying later without leaving Postgres, Apache AGE is the official graph-extension example, but it is still an extension on top of Postgres rather than a reason to abandon Postgres.

## Suggested Data Model Primitives

Keep the model small and explicit:

- `Person`: canonical human identity
- `SourceProfile`: one row per source-specific profile or record
- `Paper`: paper or publication entity
- `Affiliation`: institution or org entity
- `Email`: observed email address
- `URL`: observed homepage or profile URL
- `Evidence`: immutable observation with source pointer, raw payload reference, timestamps, and confidence
- `PersonAffiliation`, `PersonPaper`, `PersonEmail`, `PersonURL`: edge tables for canonical links
- `MergeDecision`: who merged what, when, and why
- `Conflict`: competing claims that were not yet resolved or were rejected

Rule of thumb: store **observations** append-only, derive the **current canonical view** from them.

## Risks

- False merges if confidence is allowed to overwrite evidence too early.
- History loss if the canonical person row becomes the only place facts live.
- Operational drag if a graph engine is added before query patterns justify it.
- Split-brain semantics if raw staging, canonical storage, and graph storage all try to act as source of truth.
- Memory pressure and separate ops complexity if Memgraph is chosen for a workload that does not truly need it.

## Sources Reviewed

- Neo4j property graph and constraint/MERGE docs: https://assets.neo4j.com/Official-Materials/Property%2BGraph%2B-%2BBehind%2Bthe%2BScenes.pdf and https://neo4j.com/docs/cypher-manual/current/clauses/merge/ and https://neo4j.com/docs/cypher-manual/current/constraints/managing-constraints/
- Memgraph official site and download hub: https://memgraph.com/ and https://memgraph.com/download and https://memgraph.com/data-lineage
- Apache AGE overview and FAQ: https://age.apache.org/overview/ and https://age.apache.org/faq/
- PostgreSQL docs for `jsonb`, `ON CONFLICT`, foreign keys, and recursive queries: https://www.postgresql.org/docs/current/static/datatype-json.html and https://www.postgresql.org/docs/current/sql-insert.html and https://www.postgresql.org/docs/18/ddl-constraints.html and https://www.postgresql.org/docs/17/queries-with.html
- MongoDB docs on embedding vs references as a representative document-store pattern: https://www.mongodb.com/docs/manual/data-modeling/embedding/ and https://www.mongodb.com/docs/manual/data-modeling/referencing/
