// 1. Inmunidad Diplomática (Constraints & Indexes)
// Crear restricciones de unicidad (Indices rápidos)
CREATE CONSTRAINT citizen_id IF NOT EXISTS FOR (c:Citizen) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT crime_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE;

// 2. Génesis de la Ciudad (Creación de Nodos)
// Crear Ciudadanos (Nodos Azules)
UNWIND range(1, 100) AS i
CREATE (:Citizen {
    id: i,
    name: "Citizen_" + i,
    risk_base: 0.1, // Probabilidad base baja
    status: "Active"
});

// Crear Ubicaciones (Nodos Amarillos)
UNWIND ["Bank", "Alley", "Subway Station", "Jewelry Store", "Park"] AS locType
MERGE (:Location {
    id: "LOC_" + locType,
    type: locType,
    security_level: toInteger(rand() * 10) // Nivel de vigilancia 0-10
});

// 3. El Tejido Social (Relaciones Históricas)
// Generar red social aleatoria (Relación KNOWS)
MATCH (c1:Citizen), (c2:Citizen)
WHERE c1.id <> c2.id AND rand() < 0.05 // 5% de probabilidad de conocerse
MERGE (c1)-[:KNOWS {since: 2020}]->(c2);

// Historial de Movimientos (Relación WAS_AT)
MATCH (c:Citizen), (l:Location)
WHERE rand() < 0.1 // El ciudadano ha estado en este lugar
MERGE (c)-[:WAS_AT {
    timestamp: datetime(),
    duration_minutes: toInteger(rand() * 60)
}]->(l);

// 4. El Crimen Pasado (Datos de Entrenamiento)
// Crear algunos criminales convictos y sus delitos pasados
MATCH (c:Citizen {id: 10}), (l:Location {type: "Bank"})
MERGE (c)-[:COMMITTED_CRIME {
    date: date('2025-01-01'),
    type: "Robbery",
    severity: 9
}]->(l);

MATCH (c:Citizen {id: 42}), (l:Location {type: "Alley"})
MERGE (c)-[:COMMITTED_CRIME {
    date: date('2025-02-15'),
    type: "Assault",
    severity: 7
}]->(l);
