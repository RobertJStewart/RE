# Update.py Script Flow Diagram

## 🔄 Enhanced Data Ingestion Workflow

```mermaid
graph TB
    %% Enhanced Data Ingestion Flow
    A[Start Ingestion] --> B{Master Copy Exists?}
    
    %% First Run Path
    B -->|No| C[First Run Mode]
    C --> D[Download Data]
    D --> E[Get Geography-Specific Critical Columns]
    E --> F[Validate Data Against Critical Columns]
    F --> G[Create Master Copy]
    G --> H[Clean Data]
    H --> I[Continue Pipeline]
    
    %% Subsequent Run Path
    B -->|Yes| J[Subsequent Run Mode]
    J --> K[Download New Data]
    K --> L[Get Geography-Specific Critical Columns]
    L --> M[Load Master Copy]
    M --> N[Compare Data Continuity]
    N --> O{Recent Data Match?}
    
    %% Continuity Validation
    O -->|Yes| P[Update Master Copy]
    O -->|No| Q[Data Discontinuity Error]
    Q --> R[Quit Pipeline]
    R --> S[Future Development Goal]
    
    %% Success Path
    P --> T[Clean Data]
    T --> U[Continue Pipeline]
    
    %% Styling - Optimized for dark backgrounds
    classDef entry fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef process fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef decision fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef error fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#ffffff
    classDef success fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#ffffff
    
    class A entry
    class B,O decision
    class C,D,E,F,G,J,K,L,M,N,P,T process
    class Q,R,S error
    class I,U success
```

## 🗺️ Dynamic Critical Columns Validation

```mermaid
graph TB
    %% Dynamic Critical Columns Flow
    A[Start Data Validation] --> B[Get Geography Level]
    B --> C{Geography Type?}
    
    %% Geography-Specific Paths
    C -->|Metro| D[Metro Critical Columns:<br/>RegionID, RegionName, StateName,<br/>Metro, CountyName, SizeRank]
    C -->|State| E[State Critical Columns:<br/>RegionID, RegionName, StateName, SizeRank]
    C -->|County| F[County Critical Columns:<br/>RegionID, RegionName, StateName,<br/>CountyName, SizeRank]
    C -->|City| G[City Critical Columns:<br/>RegionID, RegionName, StateName,<br/>CityName, SizeRank]
    C -->|ZIP| H[ZIP Critical Columns:<br/>RegionID, RegionName, StateName, SizeRank]
    C -->|Neighborhood| I[Neighborhood Critical Columns:<br/>RegionID, RegionName, StateName,<br/>NeighborhoodName, CityName, SizeRank]
    
    %% Validation Process
    D --> J[Validate Against Critical Columns]
    E --> J
    F --> J
    G --> J
    H --> J
    I --> J
    
    J --> K{All Critical Columns Present?}
    K -->|Yes| L[Identify Date Columns]
    K -->|No| M[Missing Columns Error]
    
    L --> N[Continue Data Processing]
    M --> O[Quit with Error Message]
    
    %% Styling - Optimized for dark backgrounds
    classDef entry fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef process fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef decision fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef error fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#ffffff
    classDef success fill:#14532d,stroke:#22c55e,stroke-width:2px,color:#ffffff
    classDef geography fill:#1e40af,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    
    class A entry
    class B,C,K decision
    class D,E,F,G,H,I geography
    class J,L,N process
    class M,O error
    class N success
```

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

## DataConnection Integration in ETL Pipeline

### DataConnection Class Hierarchy in Pipeline Context

```mermaid
graph TD
    A[ETL Pipeline Start] --> B[Initialize DataIngestion]
    B --> C[Create REDataConnection]
    C --> D[Initialize ZillowDataConnection]
    D --> E[Load Available Combinations]
    E --> F[Create Data Source Configs]
    
    F --> G[Process Each Data Source]
    G --> H[Extract data_source, data_type, sub_type, geography]
    H --> I[Get Metadata from DataConnection]
    I --> J[Check Connection Health]
    J --> K[Download Data or Use Fallback]
    K --> L[Process and Clean Data]
    L --> M[Save Master Copy]
    M --> N[Save Processed Data]
    
    classDef pipeline fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef re fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef zillow fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef process fill:#dc2626,stroke:#ef4444,stroke-width:2px,color:#ffffff
    
    class A,B pipeline
    class C,D,E,F re
    class I,J zillow
    class G,H,K,L,M,N process
```

### DataConnection Method Flow in Pipeline

```mermaid
sequenceDiagram
    participant ETL as ETL Pipeline
    participant DI as DataIngestion
    participant RE as REDataConnection
    participant ZD as ZillowDataConnection
    participant DC as Data Source
    
    ETL->>DI: Initialize with data path
    DI->>RE: Create REDataConnection
    RE->>ZD: Initialize ZillowDataConnection
    ZD->>RE: Return available combinations
    RE->>DI: Return 37 combinations
    
    loop For each data source
        DI->>RE: get_metadata(data_source, data_type, sub_type, geography)
        RE->>ZD: get_metadata(data_type, sub_type, geography)
        ZD->>RE: Return DataSourceMetadata
        RE->>DI: Return metadata
        
        DI->>RE: check_connection_health(data_source, data_type, sub_type, geography)
        RE->>ZD: check_connection_health(data_type, sub_type, geography)
        ZD->>DC: Test connection methods
        DC->>ZD: Return health status
        ZD->>RE: Return health status
        RE->>DI: Return health status
        
        alt Connection Healthy
            DI->>DC: Download data
            DC->>DI: Return data
        else Connection Unhealthy
            DI->>DI: Use fallback procedures
            DI->>DI: Generate mock data
        end
        
        DI->>DI: Process and clean data
        DI->>DI: Save master copy
        DI->>DI: Save processed data
    end
```

### DataConnection Coverage in Pipeline

```mermaid
graph LR
    A[ETL Pipeline] --> B[7 Data Sources Processed]
    B --> C[zhvi_all_homes_smoothed_seasonally_adjusted]
    B --> D[zhvi_all_homes_raw_mid_tier]
    B --> E[zhvi_all_homes_top_tier]
    B --> F[zhvi_all_homes_bottom_tier]
    B --> G[zhvi_single_family_homes]
    B --> H[zhvi_condo_coop]
    B --> I[zori_all_homes]
    
    C --> J[ZIP Geography]
    D --> K[ZIP Geography]
    E --> L[ZIP Geography]
    F --> M[ZIP Geography]
    G --> N[ZIP Geography]
    H --> O[ZIP Geography]
    I --> P[ZIP Geography]
    
    J --> Q[50 rows × 16 columns]
    K --> R[50 rows × 16 columns]
    L --> S[50 rows × 16 columns]
    M --> T[50 rows × 16 columns]
    N --> U[50 rows × 16 columns]
    O --> V[50 rows × 16 columns]
    P --> W[50 rows × 16 columns]
    
    classDef pipeline fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef source fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef geography fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef output fill:#dc2626,stroke:#ef4444,stroke-width:2px,color:#ffffff
    
    class A pipeline
    class B,C,D,E,F,G,H,I source
    class J,K,L,M,N,O,P geography
    class Q,R,S,T,U,V,W output
```

### Pipeline Performance with DataConnection

```mermaid
graph TD
    A[Pipeline Start] --> B[DataConnection Initialization: ~0.01s]
    B --> C[Load 37 Available Combinations: ~0.01s]
    C --> D[Process 7 Data Sources: ~1.3s]
    D --> E[Generate Mock Data: ~0.8s]
    E --> F[Validate Data: ~0.2s]
    F --> G[Clean Data: ~0.3s]
    G --> H[Save Files: ~0.1s]
    H --> I[Generate Quality Report: ~0.1s]
    I --> J[Pipeline Complete: ~1.3s Total]
    
    classDef init fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#ffffff
    classDef process fill:#065f46,stroke:#10b981,stroke-width:2px,color:#ffffff
    classDef output fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffffff
    classDef complete fill:#dc2626,stroke:#ef4444,stroke-width:2px,color:#ffffff
    
    class A,B,C init
    class D,E,F,G,H,I process
    class J complete
```
