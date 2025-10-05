# RE Market Tool - Workflow Diagram

## 🔄 Complete System Workflow

```mermaid
graph TB
    %% External Data Sources
    A1[Zillow ZHVI Data<br/>📊 CSV Download] --> B[Data Ingestion<br/>🐍 Python Scripts]
    A2[Zillow ZORI Data<br/>📊 CSV Download] --> B
    A3[ZIP Code Coordinates<br/>🗺️ Geocoding API] --> B
    
    %% Data Ingestion Details
    B --> B1[Data Validation<br/>🔍 Pandas/NumPy]
    B1 --> B2[Data Cleaning<br/>🧹 Custom Scripts]
    B2 --> B3[Coordinate Matching<br/>📍 H3 Geospatial]
    
    %% Backend Processing Pipeline
    B3 --> C[Geographic Aggregation<br/>🗺️ H3 + Custom Logic]
    C --> D[Statistical Calculation<br/>📈 Pandas + NumPy]
    D --> E[Static File Generation<br/>📁 JSON/GeoJSON Export]
    
    %% Geographic Aggregation Levels
    C --> C1[Region Level<br/>🌎 Multi-State Groups]
    C --> C2[State Region Level<br/>🗺️ State Subdivisions]
    C --> C3[State Level<br/>🏛️ Individual States]
    C --> C4[ZIP Code Level<br/>📮 Individual ZIPs]
    
    %% Statistical Methods Applied
    D --> D1[Average Calculation<br/>📊 Mean Values]
    D --> D2[Median Calculation<br/>📊 50th Percentile]
    D --> D3[Min/Max Values<br/>📊 Range Analysis]
    D --> D4[Count Statistics<br/>📊 Data Points]
    D --> D5[Standard Deviation<br/>📊 Variance Analysis]
    
    %% Generated Static Files
    E --> E1[Region JSON<br/>📄 regions.json]
    E --> E2[State Region JSON<br/>📄 state_regions.json]
    E --> E3[State JSON<br/>📄 states.json]
    E --> E4[ZIP GeoJSON<br/>🗺️ zip_latest.geojson]
    E --> E5[Statistics JSON<br/>📊 statistics.json]
    E --> E6[Metadata JSON<br/>📋 metadata.json]
    
    %% Frontend Application Structure
    E1 --> F[Frontend Overview<br/>🌐 HTML/CSS/JS]
    E2 --> F
    E3 --> F
    E4 --> F
    E5 --> F
    E6 --> F
    
    E1 --> G[Frontend Time Series<br/>📈 Interactive Charts]
    E2 --> G
    E3 --> G
    E4 --> G
    E5 --> G
    E6 --> G
    
    %% User Interface Components
    F --> H[Overview Dashboard<br/>📊 Summary Views]
    G --> I[Time Series Analysis<br/>📈 Trend Visualization]
    
    H --> J[User Interface<br/>🖥️ Web Browser]
    I --> J
    
    %% Dark Theme Optimized Styling
    classDef dataSource fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#e2e8f0
    classDef ingestion fill:#1a365d,stroke:#2b6cb0,stroke-width:2px,color:#e2e8f0
    classDef processing fill:#2d1b69,stroke:#553c9a,stroke-width:2px,color:#e2e8f0
    classDef aggregation fill:#1a202c,stroke:#4a5568,stroke-width:2px,color:#e2e8f0
    classDef statistics fill:#2d3748,stroke:#68d391,stroke-width:2px,color:#e2e8f0
    classDef files fill:#1a365d,stroke:#4299e1,stroke-width:2px,color:#e2e8f0
    classDef frontend fill:#553c9a,stroke:#9f7aea,stroke-width:2px,color:#e2e8f0
    classDef ui fill:#2d3748,stroke:#f6e05e,stroke-width:2px,color:#e2e8f0
    
    class A1,A2,A3 dataSource
    class B,B1,B2,B3 ingestion
    class C,C1,C2,C3,C4 processing
    class D,D1,D2,D3,D4,D5 aggregation
    class E,E1,E2,E3,E4,E5,E6 statistics
    class F,G files
    class H,I frontend
    class J ui
```

## 🏗️ Backend Processing Pipeline

```mermaid
graph LR
    %% Input Sources
    A1[Zillow ZHVI CSV<br/>📊 Home Values] --> B[Python Ingestion<br/>🐍 zillow_ingest.py]
    A2[Zillow ZORI CSV<br/>📊 Rental Rates] --> B
    A3[ZIP Coordinates<br/>🗺️ Geocoding Service] --> B
    
    %% Processing Steps with Tools
    B --> C[Data Validation<br/>🔍 Pandas DataFrame]
    C --> D[Data Cleaning<br/>🧹 Custom Functions]
    D --> E[Coordinate Matching<br/>📍 H3 Geospatial Index]
    E --> F[Geographic Grouping<br/>🗺️ H3 + Custom Logic]
    F --> G[Statistical Aggregation<br/>📈 Pandas GroupBy]
    G --> H[File Generation<br/>📁 JSON/GeoJSON Export]
    
    %% Output Files
    H --> I[Static JSON Files<br/>📄 regions.json<br/>📄 states.json<br/>📄 statistics.json]
    H --> J[GeoJSON Files<br/>🗺️ zip_latest.geojson<br/>🗺️ regions.geojson]
    H --> K[Metadata Files<br/>📋 metadata.json<br/>📋 config.json]
    
    %% Dark Theme Optimized Styling
    classDef input fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#e2e8f0
    classDef process fill:#1a365d,stroke:#2b6cb0,stroke-width:2px,color:#e2e8f0
    classDef output fill:#1a202c,stroke:#68d391,stroke-width:2px,color:#e2e8f0
    
    class A1,A2,A3 input
    class B,C,D,E,F,G,H process
    class I,J,K output
```

## 🎨 Frontend Architecture

```mermaid
graph TB
    %% Static Data Files
    A[Region JSON<br/>📄 regions.json] --> D[Overview Page<br/>🌐 index.html]
    B[State Region JSON<br/>📄 state_regions.json] --> D
    C[State JSON<br/>📄 states.json] --> D
    E[ZIP GeoJSON<br/>🗺️ zip_latest.geojson] --> D
    F[Statistics JSON<br/>📊 statistics.json] --> D
    G[Metadata JSON<br/>📋 metadata.json] --> D
    
    A --> H[Time Series Page<br/>📈 timeseries.html]
    B --> H
    C --> H
    E --> H
    F --> H
    G --> H
    
    %% Overview Page Components
    D --> I[Data Summary<br/>📊 Summary Cards]
    D --> J[Charts & Graphs<br/>📈 Chart.js/D3.js]
    D --> K[Data Tables<br/>📋 HTML Tables]
    
    %% Time Series Page Components
    H --> L[Interactive Map<br/>🗺️ Leaflet/Mapbox]
    H --> M[Time Slider<br/>⏰ Custom Controls]
    H --> N[Statistical Controls<br/>📊 Filter Options]
    H --> O[Export Tools<br/>💾 CSV/JSON Export]
    
    %% User Interface Assembly
    I --> P[User Interface<br/>🖥️ Web Browser]
    J --> P
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P
    
    %% Dark Theme Optimized Styling
    classDef data fill:#2d3748,stroke:#4a5568,stroke-width:2px,color:#e2e8f0
    classDef page fill:#553c9a,stroke:#9f7aea,stroke-width:2px,color:#e2e8f0
    classDef component fill:#1a365d,stroke:#4299e1,stroke-width:2px,color:#e2e8f0
    classDef ui fill:#1a202c,stroke:#f6e05e,stroke-width:2px,color:#e2e8f0
    
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
