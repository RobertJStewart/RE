# Update.py Script Flow Diagram

## 🔄 ETL Pipeline Orchestrator Flow

```mermaid
graph TB
    %% Entry Point
    A[Script Start] --> B{Parse Arguments}
    
    %% Argument Processing
    B --> C[--full]
    B --> D[--ingest-only]
    B --> E[--aggregate-only]
    B --> F[--calculate-only]
    B --> G[Default: --full]
    
    %% Pipeline Initialization
    C --> H[Initialize ETLPipeline]
    D --> H
    E --> H
    F --> H
    G --> H
    
    %% Pipeline Setup
    H --> I[Set Base Paths]
    I --> J[Ensure Directories Exist]
    J --> K[Initialize Components]
    K --> L[DataIngestion]
    K --> M[GeographicAggregation]
    K --> N[StatisticalCalculation]
    
    %% Full Pipeline Flow
    C --> O[Run Full Pipeline]
    G --> O
    O --> P[Step 1: Data Ingestion]
    P --> Q[Step 2: Geographic Aggregation]
    Q --> R[Step 3: Statistical Calculation]
    R --> S[Step 4: Generate Metadata]
    S --> T[Calculate Duration]
    T --> U[Return Success Result]
    
    %% Individual Step Flows
    D --> V[Run Ingestion Only]
    E --> W[Run Aggregation Only]
    F --> X[Run Calculation Only]
    
    V --> Y[Return Ingestion Result]
    W --> Z[Return Aggregation Result]
    X --> AA[Return Calculation Result]
    
    %% Error Handling
    P --> BB{Ingestion Success?}
    BB -->|No| CC[Log Error & Return Failure]
    BB -->|Yes| Q
    
    Q --> DD{Aggregation Success?}
    DD -->|No| CC
    DD -->|Yes| R
    
    R --> EE{Calculation Success?}
    EE -->|No| CC
    EE -->|Yes| S
    
    %% Exit
    U --> FF[Exit Code 0]
    Y --> FF
    Z --> FF
    AA --> FF
    CC --> GG[Exit Code 1]
    
    %% Styling - Optimized for dark backgrounds
    classDef entry fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef process fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef decision fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef error fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#ffffff
    classDef success fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#ffffff
    
    class A entry
    class B,H,I,J,K,L,M,N decision
    class O,P,Q,R,S,T,U,V,W,X,Y,Z,AA process
    class BB,DD,EE decision
    class CC,GG error
    class FF success
```

## 🏗️ Component Initialization Flow

```mermaid
graph LR
    A[ETLPipeline.__init__] --> B[Set Base Paths]
    B --> C[backend_path]
    B --> D[data_path]
    B --> E[aggregations_path]
    B --> F[statistics_path]
    
    C --> G[Ensure Directories]
    D --> G
    E --> G
    F --> G
    
    G --> H[Create Directory Structure]
    H --> I[Initialize DataIngestion]
    H --> J[Initialize GeographicAggregation]
    H --> K[Initialize StatisticalCalculation]
    
    I --> L[Ready for Pipeline]
    J --> L
    K --> L
    
    %% Styling - Optimized for dark backgrounds
    classDef init fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef path fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef component fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    
    class A init
    class B,C,D,E,F path
    class G,H,I,J,K,L component
```

## 📊 Full Pipeline Execution Flow

```mermaid
sequenceDiagram
    participant U as update.py
    participant I as DataIngestion
    participant A as GeographicAggregation
    participant C as StatisticalCalculation
    participant M as Metadata
    
    Note over U,M: Full Pipeline Execution
    
    U->>I: run()
    I->>I: Download & Clean CSVs
    I->>U: ingestion_result
    
    alt ingestion_result.success
        U->>A: run()
        A->>A: Create Geographic Hierarchy
        A->>U: aggregation_result
        
        alt aggregation_result.success
            U->>C: run()
            C->>C: Calculate Statistics
            C->>U: calculation_result
            
            alt calculation_result.success
                U->>M: _generate_metadata()
                M->>M: Create metadata.json
                M->>U: metadata_complete
                U->>U: Return Success
            else calculation_result.failure
                U->>U: Return Failure
            end
        else aggregation_result.failure
            U->>U: Return Failure
        end
    else ingestion_result.failure
        U->>U: Return Failure
    end
```

## 🔧 Error Handling Flow

```mermaid
graph TD
    A[Pipeline Step] --> B{Success?}
    B -->|Yes| C[Continue to Next Step]
    B -->|No| D[Log Error Details]
    D --> E[Calculate Duration]
    E --> F[Return Failure Result]
    F --> G[Exit Code 1]
    
    C --> H{More Steps?}
    H -->|Yes| A
    H -->|No| I[Generate Metadata]
    I --> J[Calculate Total Duration]
    J --> K[Return Success Result]
    K --> L[Exit Code 0]
    
    %% Styling - Optimized for dark backgrounds
    classDef process fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef decision fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef error fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#ffffff
    classDef success fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#ffffff
    
    class A,C,I,J process
    class B,H decision
    class D,E,F,G error
    class K,L success
```

## 📁 Directory Structure Created

```mermaid
graph TD
    A[ETLPipeline] --> B[backend/]
    B --> C[data/]
    B --> D[aggregations/]
    B --> E[statistics/]
    B --> F[logs/]
    
    C --> C1[raw/]
    C --> C2[processed/]
    C --> C3[coordinates/]
    
    D --> D1[regions/]
    D --> D2[state_regions/]
    D --> D3[states/]
    D --> D4[zipcodes/]
    
    E --> E1[summary.json]
    E --> E2[time_series.json]
    E --> E3[metadata.json]
    
    F --> F1[etl_pipeline.log]
    
    %% Styling - Optimized for dark backgrounds
    classDef root fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef dir fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef file fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    
    class A root
    class B,C,D,E,F,C1,C2,C3,D1,D2,D3,D4 dir
    class E1,E2,E3,F1 file
```
