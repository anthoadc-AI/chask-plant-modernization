# Prompt para Claude Code — Fase 0: Fundamentos y gobernanza

Copia y pega todo lo que está debajo de la línea en Claude Code, con la sesión
abierta en la carpeta `chask-plant-modernization` (que ya contiene `CLAUDE.md`
y los documentos fuente).

---

Lee CLAUDE.md antes de empezar. Ejecuta la **Fase 0** del proyecto: fundamentos
y gobernanza. No avances a fases posteriores. Trabaja en inglés salvo los
documentos fuente en español.

## Alcance

### 1. Estructura del repositorio
Crea exactamente esta estructura (con `.gitkeep` en carpetas vacías):

```
chask-plant-modernization/
├── .github/
│   ├── workflows/ci.yml
│   ├── ISSUE_TEMPLATE/bug_report.md
│   ├── ISSUE_TEMPLATE/feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── data/
│   ├── raw/            # dataset mensual real (mover aquí dataset_panificadora.csv)
│   ├── staging/
│   └── analytics/
├── docs/
│   └── source-documents/   # mover aquí los dos .docx originales
├── notebooks/
├── project-management/
├── src/chask/__init__.py
├── tests/test_placeholder.py
├── pyproject.toml
├── Makefile
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── .gitignore
```

### 2. Tooling
- `pyproject.toml`: paquete `chask`, versión `0.1.0`, Python >= 3.10,
  dependencias base (pandas, numpy) y grupo dev (pytest, ruff). Configuración
  de ruff (line-length 100, reglas E, F, I, N, UP) y de pytest en el mismo archivo.
- `Makefile` con targets: `install`, `lint` (ruff check + ruff format --check),
  `format` (ruff check --fix + ruff format), `test`.
- `.gitignore` para Python (venv, __pycache__, .pytest_cache, .ruff_cache,
  dist, *.egg-info, .ipynb_checkpoints, .streamlit/secrets.toml).
- `.github/workflows/ci.yml`: GitHub Actions con matriz Python 3.10/3.11/3.12,
  pasos: install → lint → test.
- `src/chask/__init__.py` con `__version__ = "0.1.0"` y
  `tests/test_placeholder.py` con un test que verifica la versión (para que CI
  tenga algo que ejecutar en verde).
- `LICENSE`: MIT, copyright Anthony Davila / INGEDAV S.R.L., 2026.

### 3. Documentos de gestión de proyectos (`project-management/`)
Redáctalos en inglés, en Markdown, usando los datos reales de los documentos
fuente en `docs/source-documents/` (léelos primero):

- `project-charter.md`: cliente, problema de negocio, objetivos, alcance,
  stakeholders, presupuesto (USD 85,000), periodo (Dec 2020 – Jun 2022),
  director de proyecto.
- `wbs.md`: desglose de trabajo de las 4 fases reales del proyecto de
  ingeniería (diagnóstico, diseño, implementación, capacitación) con
  entregables por fase.
- `schedule.md`: cronograma con diagrama Gantt en Mermaid, las 4 fases entre
  Dec 2020 y Jun 2022, hito de corte en Aug 2021.
- `risk-register.md`: tabla con 8–10 riesgos realistas del proyecto
  (probabilidad, impacto, mitigación), incluyendo los que efectivamente se
  materializaron (periodo de estabilización de maquinaria nueva con más fallas).
- `cost-baseline.md`: desglose plausible y claramente marcado como estimado de
  los USD 85,000 (fabricación de maquinaria, instalación, EMS, modernización
  eléctrica, capacitación, gestión).

### 4. README inicial
README.md conciso: título, badges (CI, license, Python versions apuntando a
`anthoadc-AI/chask-plant-modernization`), descripción de una frase del caso,
tabla de estado de fases (Fase 0 ✅, resto pendiente), estructura del repo,
instrucciones de instalación (`make install`). Se ampliará en la Fase 5.

### 5. Git y verificación final
1. Corre `make lint` y `make test`: ambos deben pasar sin errores.
2. Commits semánticos separados (mínimo: `chore: scaffold repository structure
   and tooling`, `docs: add project management baseline documents`,
   `docs: add initial README`). Nunca un solo commit gigante.
3. Tag `v0.1.0`.
4. Crea el repo público `chask-plant-modernization` en la cuenta `anthoadc-AI`
   (usa `gh repo create` si está disponible; si no, dame las instrucciones y
   espera), agrega el remote y haz push de `main` y del tag.
5. Reporta: salida de lint/test, lista de commits, URL del repo y confirmación
   de que CI corrió en verde en GitHub Actions.

## Criterios de aceptación
- `make lint` y `make test` pasan localmente.
- CI en verde en GitHub para 3.10, 3.11 y 3.12.
- Los 5 documentos de project-management existen y usan datos reales de los
  documentos fuente (sin inventar cifras nuevas).
- Ningún archivo de plantilla sin revisar, ninguna carpeta duplicada,
  ninguna URL apuntando a un repo distinto.
- Al terminar, detente y espera revisión antes de cualquier trabajo de Fase 1.
