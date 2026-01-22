# Project Pre-Crime

An experiment to recreate the "Precog System" technology from Minority Report using Graph Databases (Neo4j) and Hybrid AI (GraphSAGE, GAT, RedGAN).

## Overview

This project simulates a crime prediction system that:
1.  **Models** a city's citizens, locations, and interactions as a graph in Neo4j.
2.  **Analyzes** social connections and movements using GraphSAGE and GAT.
3.  **Predicts** potential future crimes ("Red Balls") using a GAN-based approach.

## Structure

```
Project_Pre_Crime/
├── requirements.txt    # Python dependencies
├── src/
│   ├── models.py       # GraphSAGE (Generator) and GAT (Discriminator) Models
│   ├── connector.py    # Neo4j Database Interaction
│   └── train.py        # Main Training Loop and Pre-Crime System Logic
└── scripts/
    └── setup_db.cypher # Cypher queries to initialize the Neo4j database
```

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Neo4j Setup**:
    - Ensure you have a Neo4j database running.
    - Open your Neo4j Browser.
    - Copy and paste the contents of `scripts/setup_db.cypher` to initialize the constraints, nodes, and relationships.

3.  **Run the Precog System**:
    - To test the neural architecture with dummy data (no Neo4j required for this step):
        ```bash
        python src/train.py
        ```
    - To connect to Neo4j, uncomment the `Neo4jConnector` lines in `src/train.py` and provide your database credentials.

## Components

-   **GraphSAGE (The Criminal)**: Generates embeddings to suggest potential links (intentions).
-   **GAT (The Police)**: Uses attention mechanisms to differentiate noise from real risk.
-   **RedGAN**: The adversarial process where these two compete to refine predictions.
