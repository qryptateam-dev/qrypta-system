# QRYPTA

**Simulador web didáctico para comparar la aleatoriedad de un generador clásico (PRNG) y uno cuántico simulado (QRNG), y comprobar si la Inteligencia Artificial puede distinguirlos.**

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/interfaz-Streamlit-ff4b4b)
![Licencia](https://img.shields.io/badge/licencia-todos%20los%20derechos%20reservados-lightgrey)

🇪🇸 Español · [🇬🇧 English](README.en.md)

---

## Descripción

QRYPTA es un simulador web interactivo de acceso público, pensado para estudiantes de Ingeniería en Informática de la Universidad Columbia del Paraguay (sede San Lorenzo). Genera claves con un PRNG clásico y con un QRNG simulado **bajo los mismos parámetros**, las somete a pruebas estadísticas de aleatoriedad y entrena cuatro modelos de aprendizaje automático para que intenten adivinar de qué generador salió cada clave.

El proyecto es el desarrollo práctico de un Trabajo de Conclusión de Carrera (TCC), 2026.

> **Alcance pedagógico.** Detectar una diferencia estadística entre generadores **no** equivale a romper una clave ni constituye un ataque criptográfico. El simulador estudia la detección de patrones.

## Recorrido de la aplicación

La interfaz (Streamlit) tiene seis vistas, cada una con objetivo, interpretación automática de los resultados y ayudas de lectura:

| Vista | Qué hace |
|---|---|
| 1. Inicio y Guía de Uso | Conceptos clave (bits, semilla, qubits, entropía, p-valor, clasificadores) y un cuestionario breve. |
| 2. Laboratorio de Generación de Claves | Genera 100, 1.000 o 10.000 claves de 64, 128 o 256 bits por generador. La semilla del PRNG puede ser un número, un texto corto (convertido con SHA-256) o automática. Muestra histogramas y mapas de frecuencia de bytes. |
| 3. Análisis de Entropía y Aleatoriedad | Entropía de Shannon (por bit y por byte), proporción de unos, pruebas NIST SP 800-22 Monobit y de rachas, y autocorrelación en 16 desplazamientos. |
| 4. Clasificación con IA | Resume cada clave en 12 indicadores y entrena Árbol de Decisión, Random Forest, SVM lineal y Red Neuronal (MLP) con partición 70/30 estratificada. Reporta precisión, sensibilidad, especificidad y p-valor binomial frente al azar. Incluye una serie por volumen (100, 1.000 y 10.000 claves). |
| 5. Dashboard e Informe | Comparación entre generadores, matrices de confusión, conclusión automática y exportación del informe en **CSV verificable** y **PDF de lectura**. |
| 6. Verificar Informe | Verificación pública, individual o en lote (hasta 50 CSV), con alertas por contenido modificado, ventana de entrega, semillas asignadas y archivos duplicados o reexportados. |

## Módulos

| Módulo | Archivo | Descripción |
|---|---|---|
| M1 | `core/prng.py` | PRNG clásico Mersenne Twister (MT19937) e interpretación de la semilla |
| M2 | `core/qrng.py` | QRNG simulado: compuertas Hadamard sobre 16 qubits y medición en Qiskit Aer |
| M3 | `core/estadistica.py` | Entropía, frecuencia, autocorrelación, NIST Monobit y rachas, indicadores por clave |
| M4 | `core/ml.py` | Clasificación del origen de cada clave con cuatro modelos de Scikit-Learn |
| M5 | `core/experimento.py` | Experimentos controlados y reproducibles, y serie por volumen de datos |
| M6 | `core/informe.py`, `core/verificacion.py` | Conclusión automática, CSV/PDF y código de verificación HMAC-SHA256 |
| M7 | `app/` | Interfaz web pedagógica en Streamlit |
| M8 | `Dockerfile`, `politica_limpieza.json` | Contenedor y despliegue en Google Cloud Run |

Todos los parámetros del experimento (longitudes, volúmenes, qubits, α = 0,01, partición, semilla de los modelos) están centralizados en `core/config.py`.

## Estructura del repositorio

```
app/                 Interfaz Streamlit (main.py, estado de sesión, textos didácticos y vistas/)
core/                Lógica del simulador, independiente de la interfaz
scripts/             generar_muestra.py: muestra del estudio (se ejecuta localmente)
tests/               Pruebas de core y de la app (pytest + streamlit.testing)
.streamlit/          Configuración de Streamlit (sin telemetría, tema)
env.yaml.ejemplo     Plantilla de variables de entorno para Cloud Run
politica_limpieza.json  Política de limpieza de imágenes en Artifact Registry
```

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.11 |
| Simulación cuántica | Qiskit 2.4 + Qiskit Aer |
| Interfaz web | Streamlit |
| Inteligencia artificial | Scikit-Learn |
| Estadística y datos | NumPy, SciPy, pandas |
| Visualización | Plotly (app), Matplotlib (PDF) |
| Informe PDF | fpdf2 |
| Verificación de informes | HMAC-SHA256 (módulos `hmac`, `hashlib` y `secrets`) |
| Contenedores y nube | Docker, Google Cloud Run |

Las versiones están fijadas en `requirements.txt`. Qiskit se fija en 2.4.2 a propósito: la serie 2.5.x falla cuando Streamlit importa y usa el simulador en hilos distintos (ver `tests/test_core.py`).

La arquitectura es **sin estado (stateless)**: no hay base de datos ni inicio de sesión. El experimento vive en `st.session_state` y se pierde al cerrar la pestaña, y los informes se verifican recalculando la firma, no consultando un registro.

## Ejecución local

```bash
git clone https://github.com/qryptateam-dev/qrypta-system.git
cd qrypta-system
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

La exportación y la verificación de informes necesitan la clave secreta en la variable `QRYPTA_HMAC_KEY`. Para generar una:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
export QRYPTA_HMAC_KEY="<clave generada>"     # En Windows (PowerShell): $env:QRYPTA_HMAC_KEY="<clave>"
streamlit run app/main.py
```

### Pruebas

```bash
pip install pytest
python -m pytest
```

### Muestra del estudio

`scripts/generar_muestra.py` ejecuta 30 repeticiones por volumen (90 experimentos con claves de 256 bits) y guarda los CSV firmados, el detalle, el resumen y la decisión por condición (con corrección de Bonferroni) en la carpeta `muestra/`, que no se sube al repositorio:

```bash
python -m scripts.generar_muestra --repeticiones 30 --salida muestra
```

## Docker y Google Cloud Run

```bash
docker build -t qrypta .
docker run --rm -p 8080:8080 -e QRYPTA_HMAC_KEY="<clave>" qrypta
```

La app queda disponible en `http://localhost:8080`. Para desplegar en Cloud Run, copiá `env.yaml.ejemplo` como `env.yaml` (está en `.gitignore`), reemplazá el valor de la clave y ejecutá:

```bash
gcloud run deploy qrypta --source . --region <region> --allow-unauthenticated --env-vars-file env.yaml
```

`politica_limpieza.json` conserva las dos imágenes más recientes en Artifact Registry y borra el resto:

```bash
gcloud artifacts repositories set-cleanup-policies <repositorio> --location <region> --policy politica_limpieza.json
```

La clave HMAC nunca entra en la imagen ni en el repositorio.

## Autores

| Integrante | Módulos |
|---|---|
| Larissa Aiko Kian | M1, M2, M3, M8 |
| Anthony Ojeda | M4, M5, M6, M7 |

Universidad Columbia del Paraguay · Ingeniería en Informática · Sede San Lorenzo · 2026

## Licencia

Copyright © 2026 Larissa Aiko Kian y Anthony Ojeda. **Todos los derechos reservados.** El código se publica para consulta y evaluación académica; para reutilizarlo, contactá a los autores. Ver [LICENSE](LICENSE).

Las dependencias de terceros conservan sus propias licencias (Python: PSF; Qiskit, Qiskit Aer, Streamlit y Docker: Apache 2.0; Scikit-Learn, NumPy, SciPy y pandas: BSD; Plotly: MIT; Matplotlib: licencia propia compatible con PSF; fpdf2: LGPL 3.0).
