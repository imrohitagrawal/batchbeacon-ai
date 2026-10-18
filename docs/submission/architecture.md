# Deployed architecture and journey

The accepted demonstration runs one Cloud Run application. Model proposals do not
authorize actions; deterministic server checks and explicit human confirmation do.
The diagram describes the delivered historical-source scope. Consumer discovery
and automated source-image ingestion remain in the [future roadmap](consumer-recall-explorer-roadmap.md).

```mermaid
flowchart LR
    subgraph guest[Guest boundary]
        U[Retail console\nSynthetic shop]
    end
    subgraph app[One Cloud Run application]
        W[Retail UI, queue and owned sessions]
        A[Bounded ADK extraction workflow]
        V[Deterministic verifier\nCurrentness and action controls]
        W --> A
        A -->|Untrusted field proposals| V
    end
    U -->|Label evidence and explicit confirmation| W
    A <-->|Managed inference| G[Vertex AI\nGemini 3.8 Flash]
    S[Reviewed historical notice versions\nSource review boundary] --> V
    V -->|Owned records and transactions| F[Firestore]
    W -->|Validated image uploads| C[Private Cloud Storage]
    C -->|Normalized image bytes| A
    app -.->|Technical evidence| O[Private Operations\nOutside guest boundary]
    V -->|Simulated action and owned queue| W
```

```mermaid
flowchart LR
    A[1. Capture synthetic label] --> B[2. Gemini proposes fields\nOne bounded ADK workflow]
    B --> C[3. Server verifies\nIdentity before lot, date and scope]
    C -->|Supported match| D[4. Person reviews and confirms\nExplicit simulated hold]
    C -->|Missing, stale or unsupported| R[Review required]
    D --> E[5. Firestore saves\nEvidence and action]
    E --> F[6. Owned queue resumes\nSame investigation after refresh]
```

Private Operations contains verified resource/monitoring-policy subsets. Full
application telemetry and alert firing/closure are not claimed. See [release scope](release-scope.md).
