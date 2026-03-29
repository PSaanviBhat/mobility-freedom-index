    A[🧑‍💻 User Input: Start, End, Time] --> B[🗺️ Backend: Fetch Route Nodes]
    B --> C[⚙️ Feature Engine: Apply Time Modifiers & Aggregate]
    C --> D[📊 14-Feature Vector Built]
    D --> E[🧠 XGBoost Inference Pipeline]
    E --> F[🎲 Raw Risk Probability 0.0 - 1.0]
    F --> G{🛡️ Is Probability >= 0.07?}
    
    G -- Yes --> H[🔴 Flag: High Risk]
    G -- No --> I[🟢 Flag: Safe]
    
    H --> J[💯 Calculate Freedom Score]
    I --> J
    
    J --> K[📱 Frontend: Render Map Polylines]

    style A fill:#1e1e1e,stroke:#fff,stroke-width:2px,color:#fff
    style G fill:#f39c12,stroke:#fff,stroke-width:2px,color:#000
    style H fill:#e74c3c,stroke:#fff,stroke-width:2px,color:#fff
    style I fill:#2ecc71,stroke:#fff,stroke-width:2px,color:#000
    style K fill:#3498db,stroke:#fff,stroke-width:2px,color:#fff
