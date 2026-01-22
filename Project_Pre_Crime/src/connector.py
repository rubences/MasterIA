from neo4j import GraphDatabase

class Neo4jConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def update_predictions(self, predictions_list):
        """
        Recibe una lista de diccionarios: [{'source': ID, 'target': ID, 'risk': 0.95}, ...]
        Crea relaciones WILL_COMMIT marcadas en ROJO.
        """
        query = """
        UNWIND $batch as row
        MATCH (p:Person {id: row.source})
        MATCH (l:Location {id: row.target})
        MERGE (p)-[r:WILL_COMMIT]->(l)
        SET r.risk_score = row.risk,
            r.color = '#FF0000',  // Rojo "Minority Report"
            r.timestamp = timestamp()
        """
        with self.driver.session() as session:
            session.run(query, batch=predictions_list)
            print(f"{len(predictions_list)} predicciones de crimen insertadas en Neo4j.")
