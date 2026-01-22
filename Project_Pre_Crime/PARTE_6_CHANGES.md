"""
Parte 6: Expandiendo el Mundo - Locations & Crimes

=== CAMBIOS INTRODUCIDOS ===

1. REORGANIZACIÓN DE SCHEMAS
   - Divididos en archivos especializados:
     * schemas_citizen.py: Ciudadanos (ya existía, separado)
     * schemas_location.py: NUEVO - Ubicaciones
     * schemas_crime.py: NUEVO - Eventos criminales
     * schemas.py: Punto de entrada central (re-exporta todo para compatibilidad)
   
   - Nuevos tipos enumerados:
     * LocationType: BANK, ALLEY, PARK, STREET, STORE, PARKING, RESIDENTIAL, COMMERCIAL, INDUSTRIAL
     * CrimeType: ROBBERY, ASSAULT, THEFT, MURDER, FRAUD, VANDALISM, ARSON, BURGLARY, DUI, HOMICIDE

2. NUEVOS SCHEMAS

   A. LOCATIONS (app/models/schemas_location.py)
      - Location: Ubicación con id, name, type, env_risk, coordinates, crime_counts, risk_level
      - LocationCreate: Para POST (sin id, con coordinates)
      - LocationHotspot: Resultado de análisis de hotspots
      - LocationStatistics: Estadísticas agregadas
      - CoordinateBase: Latitud/Longitud para geolocalización

   B. CRIMES (app/models/schemas_crime.py)
      - Crime: Evento criminal completo
      - CrimeCreate: Para POST (necesita date, location_id, type, severity)
      - CrimeReport: Crimen + análisis de impacto + ciudadanos relacionados
      - CrimeStatistics: Estadísticas de crímenes
      - CrimeTimeline: Análisis temporal por día

3. REPOSITORIES

   A. LocationRepository (app/repositories/location_repo.py)
      Métodos Cypher:
      - find_all(): Todas las ubicaciones
      - find_by_id(id): Ubicación específica
      - find_hotspots(limit): Ubicaciones de alto riesgo
      - find_by_name(name): Búsqueda por nombre
      - find_nearby_crimes(location_id, days): Crímenes recientes
      - create(data): Crear ubicación
      - count_all(): Total de ubicaciones
      - get_statistics(): Estadísticas agregadas
      
      Cálculo de riesgo:
      - Score = (crime_count * 0.6) + (recent_count * 0.3) + (env_risk * 10 * 0.1)
      - CRITICAL: >= 15, HIGH: >= 10, MEDIUM: >= 5, LOW: < 5

   B. CrimeRepository (app/repositories/crime_repo.py)
      Métodos Cypher:
      - find_all(limit): Todos los crímenes
      - find_by_id(id): Crimen específico
      - find_recent_activity(days, limit): Actividad reciente
      - find_by_type(type, days): Crímenes de un tipo
      - find_by_location(location_id): Crímenes en ubicación
      - find_by_perpetrator(perp_id): Historial de un ciudadano
      - create(data): Registrar crimen
      - count_all(): Total de crímenes
      - count_by_type(): Crímenes por tipo
      - get_statistics(days): Estadísticas
      - get_timeline(period_days): Línea temporal
      - mark_investigated(crime_id): Marcar investigado
      - find_related_citizens(crime_id): Perpetrador, víctimas, testigos

4. SERVICIOS

   A. LocationService (app/services/location_service.py)
      Métodos:
      - get_all_locations(): Lista con enriquecimiento
      - get_location(id): Detalle con crímenes recientes
      - search_locations(name): Búsqueda
      - get_hotspots(limit): Ubicaciones de riesgo
      - get_location_crimes(id, days): Historial criminal
      - create_location(data): Crear ubicación
      - get_statistics(): Estadísticas globales
      - _calculate_risk_level(): Lógica de cálculo de riesgo

   B. CrimeService (app/services/crime_service.py)
      Métodos:
      - get_all_crimes(limit): Lista de crímenes
      - get_crime(id): Detalle de crimen
      - get_recent_activity(days, limit): Actividad reciente
      - get_crimes_by_type(type, days): Por tipo
      - get_crimes_at_location(location_id): Por ubicación
      - get_perpetrator_history(perp_id): Historial del ciudadano
      - report_crime(data): Registrar crimen (orquesta creación + análisis)
      - get_crime_statistics(days): Estadísticas
      - get_crime_timeline(days): Línea temporal
      - mark_investigated(crime_id): Marcar como investigado
      - _calculate_risk_impact(): Impacto de crimen en riesgo local

5. ROUTERS (REST API)

   A. /locations (app/routers/locations.py)
      GET    /locations                    → Todas las ubicaciones
      GET    /locations/{id}               → Ubicación específica
      GET    /locations/search?q=...       → Búsqueda por nombre
      GET    /locations/hotspots?limit=10  → Hotspots de crimen
      GET    /locations/{id}/crimes        → Historial criminal
      POST   /locations                    → Crear ubicación
      GET    /locations/admin/statistics   → Estadísticas

   B. /crimes (app/routers/crimes.py)
      GET    /crimes                       → Todos los crímenes
      GET    /crimes/recent?days=30        → Actividad reciente
      GET    /crimes/type/{type}           → Por tipo de crimen
      GET    /crimes/location/{id}         → En ubicación
      GET    /crimes/perpetrator/{id}      → Historial de ciudadano
      GET    /crimes/{id}                  → Detalle de crimen
      POST   /crimes                       → Registrar crimen
      POST   /crimes/{id}/mark-investigated → Marcar investigado
      GET    /crimes/admin/statistics      → Estadísticas
      GET    /crimes/admin/timeline        → Línea temporal

6. CAMBIOS EN MAIN.PY
   - Importación de nuevos routers: locations, crimes
   - Registro: app.include_router(locations.router) y crimes.router
   - Actualización de /info endpoint con nuevos recursos

7. PATRONES ARQUITECTÓNICOS UTILIZADOS

   Same as Parte 5:
   - Repository Pattern: Cypher queries organizadas en repositorios
   - Service Pattern: Lógica de negocio separada de HTTP
   - DTO Pattern: Schemas Pydantic para validación
   - Async/Await: No-blocking I/O en toda la pila
   - Singleton: db_manager para pool de conexiones
   - Separation of Concerns: Router → Service → Repository → Database

8. CARACTERÍSTICAS DE NEO4J

   Nuevos nodos:
   - Location: id, name, location_type, env_risk, latitude, longitude, created_at
   - Crime: id, date, crime_type, severity, description, created_at, investigated
   
   Nuevas relaciones:
   - (Location)-[:LOCATION_OF]->(Crime)
   - (Citizen)-[:PERPETRATOR_OF]->(Crime)
   - (Citizen)-[:HAS_WITNESS]->(Crime) [preparado para futuro]
   - (Citizen)-[:HAS_VICTIM]->(Crime) [preparado para futuro]

9. VALIDACIONES Y RESTRICCIONES

   Locations:
   - env_risk: [0.0-1.0] (factor de riesgo ambiental)
   - coordinates: latitud [-90,90], longitud [-180,180]

   Crimes:
   - severity: [1-10]
   - date: Fecha del incidente
   - perpetrator_id: Opcional (crímenes sin perpetrador conocido)

10. ESTADÍSTICAS Y ANÁLISIS

    Ubicaciones:
    - Total de ubicaciones
    - Ubicaciones con crímenes
    - Riesgo ambiental promedio
    - Hotspots con score ponderado

    Crímenes:
    - Total de crímenes
    - Promedio y máximo de severidad
    - Distribución por tipo
    - Línea temporal con tendencias

=== LISTA DE ARCHIVOS CREADOS/MODIFICADOS ===

Creados:
✅ app/models/schemas_citizen.py
✅ app/models/schemas_location.py
✅ app/models/schemas_crime.py
✅ app/repositories/location_repo.py
✅ app/repositories/crime_repo.py
✅ app/services/location_service.py
✅ app/services/crime_service.py
✅ app/routers/locations.py
✅ app/routers/crimes.py

Modificados:
✅ app/models/schemas.py (refactorizado para re-exportar)
✅ app/main.py (routers registrados, /info actualizado)

=== NEXT STEPS (PARTE 7) ===

1. Frontend Visualization
   - Dashboard interactivo con ubicaciones (mapa)
   - Gráficos de tendencias criminales
   - Timeline de eventos
   - Red de conocidos/sospechosos

2. Integración completa
   - Pruebas E2E
   - Documentación Swagger generada automáticamente
   - Ejemplos de requests

3. Mejoras futuras
   - Búsqueda geoespacial (Neo4j Spatial)
   - Alertas en tiempo real
   - Exportación de reportes
"""
