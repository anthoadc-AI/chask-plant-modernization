# Prompt para Claude Code — Fase 1: Ingeniería de datos

Copia y pega todo lo que está debajo de la línea en Claude Code, en la carpeta
del repo `chask-plant-modernization`.

---

Lee CLAUDE.md antes de empezar. Ejecuta la **Fase 1: ingeniería de datos**.
No avances a fases posteriores. Todo el código, docstrings y documentación en
inglés.

## Alcance

### 1. Configuración central (`src/chask/config.py`)
- Rutas del proyecto (RAW_DIR, STAGING_DIR, ANALYTICS_DIR) resueltas desde la
  raíz del repo, sin rutas absolutas hardcodeadas.
- Constantes del caso: `INTERVENTION_CUTOFF = "2021-08-31"`, nombres de
  columnas del dataset, seed global `RANDOM_SEED = 42`.

### 2. Pipeline raw → staging → analytics (`src/chask/pipeline/`)
Patrón medallion simplificado, cada capa con su módulo:

- `ingest.py`: carga `data/raw/dataset_panificadora.csv` con tipos explícitos
  y parsing de fechas. Falla con error claro si el archivo no existe o el
  esquema no coincide.
- `validate.py`: validación de esquema con **pandera** (agregar a
  dependencias). Esquema del dataset mensual: tipos, columnas obligatorias,
  rangos plausibles (produccion_kg > 0, consumo_kwh > 0, fallas >= 0, etc.),
  fechas únicas y continuas mes a mes (ene 2020 – may 2022, 29 filas, fin de mes).
- `transform.py`: genera la capa staging (dataset validado y tipado, guardado
  en `data/staging/monthly_validated.csv`) y la capa analytics con features
  derivadas: `intensity_kwh_kg`, `gross_margin_pct`, `profit_usd`,
  `period` (pre/post según cutoff), `cost_per_kg`. Guardar en
  `data/analytics/monthly_enriched.csv`.
- `run.py`: orquestador que ejecuta ingest → validate → transform e imprime un
  resumen (filas procesadas, checks pasados, archivos escritos). Exponer como
  entry point o ejecutable vía `python -m chask.pipeline.run`.

### 3. Generador de dataset sintético diario (`src/chask/datagen/synthetic.py`)
- Genera `data/analytics/daily_synthetic.csv` (ene 2020 – may 2022, ~880 filas
  diarias) **calibrado contra los agregados mensuales reales**:
  - La suma diaria de produccion, consumo, ventas y costos de cada mes debe
    coincidir exactamente con el valor mensual real (distribuir con pesos por
    día de semana + ruido, luego reescalar al total mensual).
  - Fallas de máquina como eventos discretos distribuidos en el mes (el conteo
    mensual debe coincidir); cada día de falla agrega horas de inactividad y
    un pico de consumo, respetando los totales mensuales.
  - Estacionalidad semanal realista para una panificadora (mayor producción
    viernes-sábado, menor los domingos).
- Seed fija desde config (reproducible: dos ejecuciones producen el mismo CSV).
- Añadir columna `is_synthetic = True` y comentario de cabecera o nota en el
  data dictionary. El nombre del archivo ya declara que es sintético.
- Exponer vía `python -m chask.datagen.synthetic`.

### 4. Diccionario de datos (`docs/data-dictionary.md`)
- Tabla por dataset (raw mensual, staging, analytics enriquecido, sintético
  diario): columna, tipo, unidad, descripción, fuente/derivación.
- Sección explícita "Synthetic data disclosure": qué es sintético, cómo se
  generó, con qué está calibrado, seed, y para qué análisis se usa.
- Sección "Known data caveats": n=9 post-intervención, el periodo post incluye
  estabilización de maquinaria nueva (fallas más altas), y la distinción entre
  cifras del dataset mensual y cifras de estado estacionario del informe de
  ingeniería.

### 5. Tests y calidad (`tests/`)
- Tests unitarios de cada módulo del pipeline (ingest, validate, transform)
  usando fixtures con datos pequeños, más tests contra el dataset real.
- Tests del generador sintético: reproducibilidad (mismo seed → mismo output)
  y calibración (agregados mensuales del sintético == valores reales, con
  tolerancia por redondeo en flotantes).
- Test de calidad de datos que corre en CI: sin nulos, rangos, continuidad
  temporal, 29 filas.
- Objetivo: ~30–40 tests nuevos, todos en verde.

### 6. Makefile y CI
- Nuevos targets: `pipeline` (corre el pipeline completo) y `datagen`
  (genera el sintético).
- CI actualizado: después de los tests, ejecutar el pipeline y el generador
  como smoke test.

### 7. Git y verificación final
1. `make lint`, `make test`, `make pipeline`, `make datagen`: todo en verde.
2. Commits semánticos separados por bloque lógico (config, pipeline, datagen,
   docs, tests). Versión del paquete a `0.2.0`, tag `v0.2.0`, push de main y tag.
3. Reporta: número de tests y resultado, resumen impreso por el pipeline,
   verificación de calibración del sintético, commits, y estado de CI en GitHub.

## Criterios de aceptación
- Pipeline reproducible de extremo a extremo con un solo comando.
- Validación pandera falla ruidosamente ante datos corruptos (test que lo
  demuestre).
- Sintético calibrado: agregados mensuales coinciden con los reales.
- Diccionario de datos completo con divulgación de datos sintéticos y caveats.
- CI verde en 3.10/3.11/3.12.
- README: fila de Fase 1 marcada ✅ en la tabla de estado.
- Al terminar, detente y espera revisión antes de la Fase 2.
