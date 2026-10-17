# SimpleCater: two roles, one secure AI workflow

```mermaid
flowchart TB
    L[Sign in] --> R[Backend session and role check]
    R --> C[Customer workspace]
    R --> O[Owner workspace]
    C --> CA[Menu · cart · own orders · own profile]
    O --> OA[Business orders · AI summary]
    subgraph LinuxONE[One LinuxONE deployment]
        API[FastAPI backend\nRole and record ownership checks]
        DB[(One SQLite database)]
        CR[Profile encryption helper\nML-KEM + AES-GCM]
        P[Predictive model\nItem pairing + verified evidence]
        G[Local generative model\nExplain totals and prediction]
        API -->|Menus and scoped orders| DB
        API -->|Authorized profile save/read| CR
        CR -->|Encrypted profile| DB
        DB -->|Scoped item history and totals| API
        API -->|Allowed item features| P
        P -->|Recommendation and reason| API
        API -->|Verified totals + predictive result| G
        G -->|Read-only summary| API
    end
    CA --> API
    OA --> API
```

Login/session verification and role-guarded pages/API boundaries are represented by the backend scaffold. Login issuance, records, encryption and models must still be completed. Browser demo simulates the two accounts; it is not actual authorization. Models get neither profiles nor database credentials. The frontend displays text only; neither model publishes content or runs commands.

Database tables: users (encrypted profile and role), businesses, menu_items, orders, order_items, sessions. No separate analytics database. One backend function prepares permitted data.

Customer flow: sign in -> select item -> model pairing + evidence -> cart -> server-priced order -> own history.
Owner flow: sign in -> own business orders -> aggregate statistics + actual predictive output -> local LLM -> summary.
Profile flow: customer authorization -> encryption/decryption helper -> stored ciphertext. Profiles never enter AI flow.

Container image currently covers core server only. Finish native dependencies/model mounts and verify runtime on LinuxONE before claiming containerized AI execution.
