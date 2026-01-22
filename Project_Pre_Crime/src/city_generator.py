"""
Pre-Crime City Generator
========================
Genera una ciudad sintética completa con ciudadanos, ubicaciones,
relaciones sociales y crímenes históricos para entrenar el sistema Pre-Crime.

Inspirado en Minority Report y basado en redes sociales realistas.
"""

import random
import time
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from faker import Faker
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
NUM_CITIZENS = 1000
NUM_LOCATIONS = 50
CRIME_RATE = 0.05  # 5% de la población son criminales activos

fake = Faker()


class PreCrimeCityGenerator:
    """Generador de ciudad sintética para Project Pre-Crime"""
    
    def __init__(self, uri=URI, auth=AUTH, num_citizens=NUM_CITIZENS, num_locations=NUM_LOCATIONS):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.num_citizens = num_citizens
        self.num_locations = num_locations
        logger.info(f"Conexión establecida a Neo4j: {uri}")
    
    def close(self):
        """Cerrar conexión a Neo4j"""
        self.driver.close()
        logger.info("Conexión cerrada")

    def clear_database(self):
        """Limpia la base de datos para empezar de cero."""
        print("🧹 Limpiando la ciudad (Base de datos)...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Base de datos limpiada")

    def create_constraints(self):
        """Crea índices para que la inserción sea rápida."""
        print("🛡️ Estableciendo leyes físicas (Indices)...")
        queries = [
            "CREATE CONSTRAINT citizen_id IF NOT EXISTS FOR (c:Citizen) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE INDEX risk_index IF NOT EXISTS FOR (c:Citizen) ON (c.risk_seed)"
        ]
        with self.driver.session() as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception as e:
                    logger.warning(f"Constraint ya existe o error: {e}")
        logger.info("Constraints e índices creados")

    def generate_locations(self):
        """Genera el escenario (Bancos, Callejones, Parques)."""
        print(f"🏢 Construyendo {self.num_locations} ubicaciones...")
        loc_types = [
            "Bank", "Jewelry Store", "Subway Station", "Dark Alley", 
            "Park", "Cafe", "Apartment Block", "Shopping Mall", 
            "Gas Station", "Warehouse"
        ]
        
        locations = []
        for i in range(self.num_locations):
            l_type = random.choice(loc_types)
            # Los callejones y almacenes tienen un factor de riesgo ambiental más alto
            if l_type in ["Dark Alley", "Warehouse"]:
                env_risk = 0.9
            elif l_type in ["Bank", "Jewelry Store"]:
                env_risk = 0.7  # Objetivos atractivos
            else:
                env_risk = 0.1
            
            locations.append({
                "id": f"LOC_{i}",
                "name": f"{fake.street_name()} {l_type}",
                "type": l_type,
                "env_risk": env_risk,
                "coord_x": fake.latitude(),
                "coord_y": fake.longitude()
            })

        query = """
        UNWIND $batch as row
        MERGE (l:Location {id: row.id})
        SET l.name = row.name, l.type = row.type, 
            l.env_risk = row.env_risk, 
            l.coord = point({latitude: toFloat(row.coord_x), longitude: toFloat(row.coord_y)})
        """
        self._batch_insert(query, locations)
        logger.info(f"{len(locations)} ubicaciones creadas")

    def generate_citizens(self):
        """
        Genera ciudadanos con una 'Semilla de Riesgo'.
        Esta semilla es la variable latente que la IA intentará descubrir.
        """
        print(f"👥 Poblando la ciudad con {self.num_citizens} ciudadanos...")
        citizens = []
        for i in range(self.num_citizens):
            # Distribución Beta: La mayoría es buena gente (riesgo bajo), 
            # pocos son muy peligrosos
            risk_seed = random.betavariate(2, 10) 
            
            citizens.append({
                "id": i,
                "name": fake.name(),
                "born": fake.year(),
                "risk_seed": risk_seed,  # <--- EL SECRETO
                "job": fake.job(),
                "address": fake.address()
            })

        query = """
        UNWIND $batch as row
        CREATE (c:Citizen {id: row.id})
        SET c.name = row.name, c.born = row.born, 
            c.risk_seed = row.risk_seed, c.job = row.job,
            c.address = row.address, c.status = 'Active'
        """
        self._batch_insert(query, citizens)
        logger.info(f"{len(citizens)} ciudadanos creados")

    def generate_social_graph(self):
        """
        Crea la red social (:KNOWS).
        Usa lógica de 'Homofilia': Criminales conocen criminales.
        """
        print("🕸️ Tejiendo la red social...")
        
        # Recuperamos los IDs y sus riesgos para calcular lógica en Python
        with self.driver.session() as session:
            result = session.run("MATCH (c:Citizen) RETURN c.id as id, c.risk_seed as risk")
            population = [{"id": r["id"], "risk": r["risk"]} for r in result]

        relationships = []
        
        for person in tqdm(population, desc="Social Links"):
            # Lógica 1: Vecinos (IDs cercanos simulan vecindario físico)
            # Lógica 2: Afinidad de riesgo (Pandillas)
            
            num_friends = random.randint(3, 15)
            potential_friends = random.sample(population, min(50, len(population)))
            
            for friend in potential_friends:
                if person["id"] == friend["id"]: 
                    continue
                
                # Probabilidad base de conexión
                prob = 0.1 
                
                # Si ambos tienen alto riesgo, es muy probable que se conozcan (Cómplices)
                if person["risk"] > 0.6 and friend["risk"] > 0.6:
                    prob += 0.5  # HOMOFILIA PROGRAMADA
                
                # Vecindario físico (IDs cercanos)
                if abs(person["id"] - friend["id"]) < 20:
                    prob += 0.2
                
                if random.random() < prob:
                    since_year = random.randint(2015, 2025)
                    relationships.append({
                        "p1": person["id"], 
                        "p2": friend["id"],
                        "since": since_year
                    })

        query = """
        UNWIND $batch as row
        MATCH (a:Citizen {id: row.p1}), (b:Citizen {id: row.p2})
        MERGE (a)-[:KNOWS {since: row.since}]->(b)
        """
        self._batch_insert(query, relationships, batch_size=1000)
        logger.info(f"{len(relationships)} relaciones sociales creadas")

    def generate_routines(self):
        """
        Genera rutinas diarias (:VISITS).
        Las personas visitan lugares regularmente (casa, trabajo, ocio).
        """
        print("🚶 Estableciendo rutinas diarias...")
        visits = []
        
        with self.driver.session() as session:
            citizens = session.run("MATCH (c:Citizen) RETURN c.id as id").value()
            locations = session.run("MATCH (l:Location) RETURN l.id as id, l.type as type").data()

        for cid in tqdm(citizens, desc="Routines"):
            # Cada persona visita 3-7 lugares regularmente
            num_places = random.randint(3, 7)
            regular_places = random.sample(locations, num_places)
            
            for place in regular_places:
                frequency = "daily" if place["type"] in ["Cafe", "Park"] else "weekly"
                visits.append({
                    "cid": cid,
                    "lid": place["id"],
                    "frequency": frequency
                })

        query = """
        UNWIND $batch as row
        MATCH (c:Citizen {id: row.cid})
        MATCH (l:Location {id: row.lid})
        MERGE (c)-[:VISITS {frequency: row.frequency}]->(l)
        """
        self._batch_insert(query, visits, batch_size=1000)
        logger.info(f"{len(visits)} rutinas establecidas")

    def generate_crimes(self):
        """
        Genera el 'Ground Truth' (:COMMITTED_CRIME).
        Solo ciudadanos con alto risk_seed cometen crímenes.
        """
        print("🚨 Generando historial criminal...")
        crimes = []
        
        # Recuperar ciudadanos de alto riesgo y ubicaciones
        with self.driver.session() as session:
            high_risk_citizens = session.run(
                "MATCH (c:Citizen) WHERE c.risk_seed > 0.6 RETURN c.id as id, c.risk_seed as risk"
            ).data()
            locations = session.run("MATCH (l:Location) RETURN l.id as id, l.type as type, l.env_risk as risk").data()

        if not high_risk_citizens:
            print("⚠️ No hay ciudadanos de alto riesgo generados.")
            logger.warning("No se generaron crímenes (no hay ciudadanos de alto riesgo)")
            return

        for criminal in high_risk_citizens:
            # Cuantos más crímenes cometa, más fácil será para GraphSAGE detectarlo
            # Criminales más peligrosos cometen más crímenes
            num_crimes = random.randint(1, int(criminal["risk"] * 10)) 
            
            for _ in range(num_crimes):
                # Prefieren ubicaciones de alto riesgo o valor
                high_value_locations = [l for l in locations if l["risk"] > 0.5]
                if high_value_locations:
                    target = random.choice(high_value_locations)
                else:
                    target = random.choice(locations)
                
                # CRIMEN CONTEXTUAL
                if target["type"] == "Bank":
                    crime_type = "Robbery"
                    severity = random.randint(7, 10)
                elif target["type"] == "Jewelry Store":
                    crime_type = "Robbery"
                    severity = random.randint(6, 9)
                elif target["type"] == "Dark Alley":
                    crime_type = "Assault"
                    severity = random.randint(4, 8)
                elif target["type"] == "Park":
                    crime_type = "Vandalism"
                    severity = random.randint(2, 5)
                else:
                    crime_type = random.choice(["Theft", "Assault", "Vandalism"])
                    severity = random.randint(3, 7)
                
                crimes.append({
                    "cid": criminal["id"],
                    "lid": target["id"],
                    "type": crime_type,
                    "severity": severity,
                    "date": fake.date_between(start_date='-2y', end_date='today').isoformat()
                })

        query = """
        UNWIND $batch as row
        MATCH (c:Citizen {id: row.cid})
        MATCH (l:Location {id: row.lid})
        MERGE (c)-[:COMMITTED_CRIME {
            date: row.date, 
            type: row.type, 
            severity: row.severity
        }]->(l)
        """
        self._batch_insert(query, crimes)
        logger.info(f"{len(crimes)} crímenes históricos generados")

    def _batch_insert(self, query, data, batch_size=500):
        """Helper para insertar datos en bloques y no saturar la RAM."""
        if not data:
            return
            
        with self.driver.session() as session:
            total = len(data)
            for i in range(0, total, batch_size):
                batch = data[i:i+batch_size]
                session.run(query, batch=batch)

    def get_statistics(self):
        """Obtiene estadísticas de la ciudad generada."""
        print("\n📊 Estadísticas de la ciudad:")
        with self.driver.session() as session:
            stats = {}
            
            # Ciudadanos
            stats['citizens'] = session.run("MATCH (c:Citizen) RETURN count(c) as count").single()["count"]
            
            # Ubicaciones
            stats['locations'] = session.run("MATCH (l:Location) RETURN count(l) as count").single()["count"]
            
            # Relaciones sociales
            stats['social_links'] = session.run("MATCH ()-[:KNOWS]->() RETURN count(*) as count").single()["count"]
            
            # Rutinas
            stats['routines'] = session.run("MATCH ()-[:VISITS]->() RETURN count(*) as count").single()["count"]
            
            # Crímenes
            stats['crimes'] = session.run("MATCH ()-[:COMMITTED_CRIME]->() RETURN count(*) as count").single()["count"]
            
            # Criminales únicos
            stats['criminals'] = session.run("MATCH (c:Citizen)-[:COMMITTED_CRIME]->() RETURN count(DISTINCT c) as count").single()["count"]
            
            # Densidad de la red
            if stats['citizens'] > 1:
                stats['network_density'] = stats['social_links'] / (stats['citizens'] * (stats['citizens'] - 1))
            
            print(f"  👥 Ciudadanos: {stats['citizens']}")
            print(f"  🏢 Ubicaciones: {stats['locations']}")
            print(f"  🤝 Conexiones sociales: {stats['social_links']}")
            print(f"  🚶 Rutinas establecidas: {stats['routines']}")
            print(f"  🚨 Crímenes históricos: {stats['crimes']}")
            print(f"  👮 Criminales únicos: {stats['criminals']} ({stats['criminals']/stats['citizens']*100:.1f}%)")
            if 'network_density' in stats:
                print(f"  🕸️ Densidad de red: {stats['network_density']:.4f}")
            
            return stats


# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    import sys
    from utils import setup_logging
    
    setup_logging()
    
    print("=" * 70)
    print("🚨 PRE-CRIME CITY GENERATOR 🚨")
    print("Generando ciudad sintética estilo Minority Report")
    print("=" * 70)
    print()
    
    # Permitir configuración desde línea de comandos
    num_citizens = int(sys.argv[1]) if len(sys.argv) > 1 else NUM_CITIZENS
    num_locations = int(sys.argv[2]) if len(sys.argv) > 2 else NUM_LOCATIONS
    
    generator = PreCrimeCityGenerator(
        num_citizens=num_citizens,
        num_locations=num_locations
    )
    
    try:
        start_time = time.time()
        
        generator.create_constraints()
        generator.clear_database()
        
        generator.generate_locations()
        generator.generate_citizens()
        generator.generate_social_graph()
        generator.generate_routines()
        generator.generate_crimes()
        
        elapsed = time.time() - start_time
        
        print()
        print("=" * 70)
        print("✅ CIUDAD GENERADA EXITOSAMENTE")
        print(f"⏱️  Tiempo total: {elapsed:.2f} segundos")
        print("=" * 70)
        
        generator.get_statistics()
        
        print()
        print("🎯 Próximos pasos:")
        print("  1. Abre Neo4j Browser: http://localhost:7474")
        print("  2. Visualiza la red criminal:")
        print("     MATCH (c1:Citizen)-[:KNOWS]-(c2:Citizen)")
        print("     WHERE c1.risk_seed > 0.7 AND c2.risk_seed > 0.7")
        print("     RETURN c1, c2 LIMIT 50")
        print("  3. Ejecuta el script de hidratación de datos:")
        print("     python src/data_hydrator.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error en generación de ciudad: {e}", exc_info=True)
        sys.exit(1)
    finally:
        generator.close()
