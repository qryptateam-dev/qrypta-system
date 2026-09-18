# QRYPTA

**Plataforma web didáctica para comparar la aleatoriedad de generadores clásicos (PRNG) y cuánticos simulados (QRNG), y su vulnerabilidad frente a Inteligencia Artificial.**

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/interfaz-Streamlit-ff4b4b)
![Licencia](https://img.shields.io/badge/licencia-todos%20los%20derechos%20reservados-lightgrey)

🇪🇸 Español · [🇬🇧 English](README.en.md)

---

## Descripción

QRYPTA es un simulador web interactivo de acceso público, pensado para estudiantes de la carrera de Ingeniería en Informática de la Universidad Columbia del Paraguay (sede San Lorenzo). Permite generar una clave criptográfica clásica (PRNG) y una clave cuántica simulada (QRNG), someter ambas a pruebas estadísticas de aleatoriedad y lanzar contra ellas un ataque predictivo basado en aprendizaje automático, para evidenciar de forma experimental la diferencia de vulnerabilidad entre los dos paradigmas.

El proyecto es el desarrollo práctico de un Trabajo de Conclusión de Carrera (TCC), 2026.

> **Alcance pedagógico.** La demostración adversarial es una simulación didáctica y acotada. No constituye un criptoanálisis validado sobre un sistema criptográfico de producción.

## ¿Qué hace?

1. **Genera** secuencias de bits con un PRNG clásico (Mersenne Twister, MT19937) y con un QRNG simulado (circuitos con compuertas Hadamard en Qiskit).
2. **Mide** su aleatoriedad con entropía de Shannon, frecuencia de bits, autocorrelación y pruebas del NIST Statistical Test Suite (Monobit, Runs).
3. **Ataca** ambas fuentes con cuatro clasificadores de Scikit-Learn (Árbol de Decisión, Random Forest, SVM lineal y Red Neuronal multicapa) y simula la reconstrucción de un mensaje cifrado con XOR (ciphertext-only y known-plaintext).
4. **Muestra** los resultados en un dashboard interactivo (Plotly) y permite descargar un informe en PDF o CSV firmado con HMAC-SHA256.
5. **Verifica**, desde una vista para docentes, la autenticidad de un informe recibido, sin almacenar datos de la sesión original.

## Módulos

| Eje | Módulo | Descripción |
|---|---|---|
| A. Motor criptográfico | M1 | Generador pseudoaleatorio clásico (Mersenne Twister, semillas configurables, cifrado XOR) |
| | M2 | Simulador de aleatoriedad cuántica (Qiskit, compuertas Hadamard, parámetro `shots`) |
| | M3 | Pruebas de entropía y aleatoriedad (Shannon, NIST) |
| B. IA y criptoanálisis | M4 | Aprendizaje automático adversario (Scikit-Learn, 70 % entrenamiento / 30 % prueba) |
| | M5 | Agente adversario y vectores de ataque sobre cifrado XOR |
| | M6 | Dashboard de analítica y métricas de vulnerabilidad, con informes firmados |
| C. Web e infraestructura | M7 | Interfaz web pedagógica (Streamlit) y verificación docente |
| | M8 | Contenedorización (Docker) y despliegue serverless (Google Cloud Run) |

## Variables del experimento

- **VI₁, generador clásico:** Mersenne Twister (MT19937), línea base.
- **VI₂, generador cuántico:** circuitos Hadamard sobre qubits en superposición, simulados en Qiskit.
- **VD, vulnerabilidad criptográfica:** entropía de Shannon, pruebas NIST y precisión (accuracy) de los modelos de IA.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.10+ |
| Simulación cuántica | IBM Qiskit |
| Interfaz web | Streamlit |
| Inteligencia artificial | Scikit-Learn |
| Datos | pandas, NumPy |
| Visualización | Plotly |
| Verificación de informes | HMAC-SHA256 (módulo `hmac` de Python) |
| Contenedores | Docker |
| Nube | Google Cloud Run |

La arquitectura es **sin estado (stateless)**: no hay base de datos y el estado vive en `st.session_state`. Esto preserva la privacidad desde el diseño, ya que no se registra ningún dato personal entre sesiones.

## Ejecución local

> El proyecto está en desarrollo. Los comandos siguientes asumen la estructura habitual de una app Streamlit y pueden cambiar.

```bash
git clone https://github.com/qryptateam-dev/qrypta-system.git
cd qrypta-system
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Si usás firma de informes, definí la clave secreta en un archivo `.env` local (nunca lo subas al repositorio).

## Docker y Google Cloud Run

```bash
docker build -t qrypta .
docker run --rm -p 8080:8080 qrypta
```

La app queda disponible en `http://localhost:8080`. Para desplegar en Google Cloud Run (requiere `gcloud` configurado):

```bash
gcloud run deploy qrypta --source . --region <region> --allow-unauthenticated
```

La clave HMAC y cualquier otro secreto se pasan como variables de entorno del servicio, nunca dentro de la imagen.

## Autores

| Integrante | Módulos |
|---|---|
| Larissa Aiko Kian | M1, M2, M3, M8 |
| Anthony Ojeda | M4, M5, M6, M7 |

Universidad Columbia del Paraguay · Ingeniería en Informática · Sede San Lorenzo · 2026

## Licencia

Copyright © 2026 Larissa Aiko Kian y Anthony Ojeda. **Todos los derechos reservados.** El código se publica para consulta y evaluación académica; para reutilizarlo, contactá a los autores. Ver [LICENSE](LICENSE).

Las dependencias de terceros conservan sus propias licencias (Python: PSF; Qiskit, Streamlit y Docker: Apache 2.0; Scikit-Learn: BSD de 3 cláusulas).
