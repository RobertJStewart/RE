# RE Market Tool - Workflow Diagram

## 🔄 Complete System Workflow

```mermaid
graph TB
    %% Data Sources
    A[Zillow CSVs] --> B[Data Ingestion]
    C[ZIP Coordinates] --> B
    
    %% Backend Processing
    B --> D[Geographic Aggregation]
    D --> E[Statistical Calculation]
    E --> F[Static File Generation]
    
    %% Geographic Levels
    D --> D1[Region Level]
    D --> D2[State Region Level]
    D --> D3[State Level]
    D --> D4[ZIP Code Level]
    
    %% Statistical Methods
    E --> E1[Average]
    E --> E2[Median]
    E --> E3[Max/Min]
    E --> E4[Count]
    E --> E5[Std Dev]
    
    %% Static Files
    F --> F1[Region JSON]
    F --> F2[State Region JSON]
    F --> F3[State JSON]
    F --> F4[ZIP GeoJSON]
    F --> F5[Statistics JSON]
    F --> F6[Metadata JSON]
    
    %% Frontend Consumption
    F1 --> G[Frontend Overview]
    F2 --> G
    F3 --> G
    F4 --> G
    F5 --> G
    F6 --> G
    
    F1 --> H[Frontend Time Series]
    F2 --> H
    F3 --> H
    F4 --> H
    F5 --> H
    F6 --> H
    
    %% User Interface
    G --> I[User Interface]
    H --> I
    
    %% Styling
    classDef backend fill:#e1f5fe
    classDef frontend fill:#f3e5f5
    classDef data fill:#e8f5e8
    classDef ui fill:#fff3e0
    
    class B,D,E,F backend
    class G,H frontend
    class A,C,F1,F2,F3,F4,F5,F6 data
    class I ui
```

## 🏗️ Backend Processing Pipeline

```mermaid
graph LR
    %% Input
    A[Raw Zillow CSVs] --> B[Data Ingestion Script]
    C[ZIP Coordinates DB] --> B
    
    %% Processing Steps
    B --> D[Clean & Validate Data]
    D --> E[Geographic Grouping]
    E --> F[Statistical Aggregation]
    F --> G[File Generation]
    
    %% Output
    G --> H[Static JSON Files]
    G --> I[GeoJSON Files]
    G --> J[Metadata Files]
    
    %% Styling
    classDef process fill:#e3f2fd
    classDef output fill:#e8f5e8
    
    class B,D,E,F,G process
    class H,I,J output
```

## 🎨 Frontend Architecture

```mermaid
graph TB
    %% Static Files
    A[Region JSON] --> D[Overview Page]
    B[State Region JSON] --> D
    C[State JSON] --> D
    E[ZIP GeoJSON] --> D
    F[Statistics JSON] --> D
    G[Metadata JSON] --> D
    
    A --> H[Time Series Page]
    B --> H
    C --> H
    E --> H
    F --> H
    G --> H
    
    %% Page Components
    D --> I[Data Summary]
    D --> J[Charts & Graphs]
    D --> K[Data Tables]
    
    H --> L[Interactive Map]
    H --> M[Time Slider]
    H --> N[Statistical Controls]
    H --> O[Export Tools]
    
    %% User Interface
    I --> P[User Interface]
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    
    %% Styling
    classDef data fill:#e8f5e8
    classDef page fill:#f3e5f5
    classDef component fill:#fff3e0
    classDef ui fill:#ffebee
    
    class A,B,C,E,F,G data
    class D,H page
    class I,J,K,L,M,N,O component
    class P ui
```

## 📊 Data Flow Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant D as Data Source
    
    Note over U,D: Data Update Cycle
    D->>B: New Zillow CSVs
    B->>B: Process & Clean Data
    B->>B: Geographic Aggregation
    B->>B: Statistical Calculation
    B->>B: Generate Static Files
    B->>F: Update Static Files
    
    Note over U,D: User Interaction
    U->>F: Open Application
    F->>F: Load Static Files
    F->>U: Display Interface
    U->>F: Interact (Zoom, Filter, etc.)
    F->>F: Process User Input
    F->>U: Update Display
```

## 🔄 Geographic Aggregation Flow

```mermaid
graph TD
    A[ZIP Code Data] --> B[State Aggregation]
    B --> C[State Region Aggregation]
    C --> D[Region Aggregation]
    
    B --> E[State Statistics]
    C --> F[State Region Statistics]
    D --> G[Region Statistics]
    
    E --> H[State JSON Files]
    F --> I[State Region JSON Files]
    G --> J[Region JSON Files]
    
    %% Statistical Methods
    E --> K[Average]
    E --> L[Median]
    E --> M[Max/Min]
    E --> N[Count]
    
    F --> O[Average]
    F --> P[Median]
    F --> Q[Max/Min]
    F --> R[Count]
    
    G --> S[Average]
    G --> T[Median]
    G --> U[Max/Min]
    G --> V[Count]
    
    %% Styling
    classDef level fill:#e3f2fd
    classDef stats fill:#e8f5e8
    classDef files fill:#fff3e0
    
    class A,B,C,D level
    class E,F,G,K,L,M,N,O,P,Q,R,S,T,U,V stats
    class H,I,J files
```

## ⚡ Performance Optimization

```mermaid
graph LR
    A[Raw Data] --> B[Pre-calculation]
    B --> C[Static Files]
    C --> D[Browser Cache]
    D --> E[Fast Loading]
    
    F[User Interaction] --> G[Frontend Processing]
    G --> H[Instant Response]
    
    %% Styling
    classDef process fill:#e3f2fd
    classDef cache fill:#e8f5e8
    classDef ui fill:#fff3e0
    
    class A,B process
    class C,D cache
    class E,F,G,H ui
```
