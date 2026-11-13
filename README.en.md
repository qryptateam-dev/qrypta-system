# QRYPTA

**An educational web simulator that compares the randomness of a classical generator (PRNG) and a simulated quantum one (QRNG), and checks whether Artificial Intelligence can tell them apart.**

![Status](https://img.shields.io/badge/status-in%20development-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![License](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)

[🇪🇸 Español](README.md) · 🇬🇧 English

---

## Overview

QRYPTA is a public, interactive web simulator aimed at Computer Engineering students at Universidad Columbia del Paraguay (San Lorenzo campus). It generates keys with a classical PRNG (Mersenne Twister) and a simulated QRNG —a model of an ideal quantum source— **under the same parameters**, runs them through statistical randomness tests, measures their linear complexity, and trains four machine-learning models to guess which generator each key came from.

The project is the practical component of a 2026 undergraduate capstone thesis (TCC).

> **Educational scope.** Detecting a statistical difference between generators does **not** mean breaking a key and is not a cryptographic attack. The simulator studies pattern detection.

> The user interface is in Spanish.

## App walkthrough

The Streamlit interface has six pages, each with a goal, automatic interpretation of the results and reading guides:

| Page | What it does |
|---|---|
| 1. Home and user guide | Key concepts (bits, seeds, qubits, entropy, p-values, classifiers) and a short quiz. |
| 2. Key generation lab | Generates 100, 1,000 or 10,000 keys of 64, 128 or 256 bits per generator. The PRNG seed can be a number, a short text (hashed with SHA-256) or automatic. Shows byte histograms and frequency maps. |
| 3. Entropy and randomness analysis | Shannon entropy (per bit and per byte), proportion of ones, NIST SP 800-22 Monobit and Runs tests, autocorrelation over 16 lags and linear complexity (Berlekamp-Massey). |
| 4. AI classification | Summarises each key in 12 features and trains a Decision Tree, Random Forest, linear SVM and neural network (MLP) on a stratified 70/30 split. Reports accuracy, sensitivity, specificity and a binomial p-value against chance. Includes a series by data volume (100, 1,000 and 10,000 keys). |
| 5. Dashboard and report | Generator comparison (including seed dependence), confusion matrices, automatic conclusion and report export as a **verifiable CSV** and a **read-only PDF**. |
| 6. Verify report | Public verification, single or batch (up to 50 CSVs), with alerts for modified content, submission window, assigned seeds and duplicated or re-exported files. |

## Modules

| Module | File | Description |
|---|---|---|
| M1 | `core/prng.py` | Classical Mersenne Twister (MT19937) PRNG and seed parsing |
| M2 | `core/qrng.py` | Simulated QRNG: Qiskit computes the state of 16 qubits with Hadamard gates and each measurement is drawn with `secrets` (the operating system's cryptographic generator) |
| M3 | `core/estadistica.py` | Entropy, frequency, autocorrelation, NIST Monobit and Runs, linear complexity, per-key features |
| M4 | `core/ml.py` | Classification of each key's source with four Scikit-Learn models |
| M5 | `core/experimento.py` | Controlled, reproducible experiments and the data-volume series |
| M6 | `core/informe.py`, `core/verificacion.py` | Automatic conclusion, CSV/PDF and HMAC-SHA256 verification code |
| M7 | `app/` | Educational Streamlit web interface |
| M8 | `Dockerfile`, `politica_limpieza.json` | Container and Google Cloud Run deployment |

All experiment parameters (lengths, volumes, qubits, α = 0.01, split, model seed) live in `core/config.py`.

## Repository layout

```
app/                 Streamlit UI (main.py, session state, teaching texts and vistas/)
core/                Simulator logic, independent of the UI
scripts/             generar_muestra.py: study sample (run locally)
tests/               Core and app tests (pytest + streamlit.testing)
docs/                Notes on methodological changes (Spanish)
.streamlit/          Streamlit configuration (no telemetry, theme)
env.yaml.ejemplo     Environment-variable template for Cloud Run
politica_limpieza.json  Artifact Registry image cleanup policy
```

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Quantum simulation | Qiskit 2.4 (`quantum_info.Statevector`) |
| Web UI | Streamlit |
| Artificial intelligence | Scikit-Learn |
| Statistics and data | NumPy, SciPy, pandas |
| Visualisation | Plotly (app), Matplotlib (PDF) |
| PDF report | fpdf2 |
| Report verification | HMAC-SHA256 (`hmac`, `hashlib` and `secrets` modules) |
| Containers and cloud | Docker, Google Cloud Run |

Versions are pinned in `requirements.txt`. Qiskit is deliberately pinned to 2.4.2: the 2.5.x series crashes when Streamlit imports and uses Qiskit on different threads (see `tests/test_core.py`).

### Why the simulated QRNG does not use Qiskit Aer

Qiskit Aer draws each measurement with an internal Mersenne Twister (`mt19937_64`): its output has linear complexity 19,937, the same structure as the classical PRNG, so the experiment would compare a Mersenne Twister with itself. The simulator therefore computes the circuit's probabilities with Qiskit and draws the measurements with `secrets`. The result is a **model of an ideal quantum source**: no seed, not repeatable and with no linear structure. It is not real quantum randomness. See [docs/cambios_qrng_y_complejidad_lineal.md](docs/cambios_qrng_y_complejidad_lineal.md) (Spanish).

The architecture is **stateless**: no database and no login. The experiment lives in `st.session_state` and is lost when the tab closes, and reports are verified by recomputing their signature, not by looking up a record.

## Running locally

```bash
git clone https://github.com/qryptateam-dev/qrypta-system.git
cd qrypta-system
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Exporting and verifying reports requires the secret key in the `QRYPTA_HMAC_KEY` variable. To generate one:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
export QRYPTA_HMAC_KEY="<generated key>"     # On Windows (PowerShell): $env:QRYPTA_HMAC_KEY="<key>"
streamlit run app/main.py
```

### Tests

```bash
pip install pytest
python -m pytest
```

### Study sample

`scripts/generar_muestra.py` runs 30 repetitions per volume (90 experiments with 256-bit keys) and writes the signed CSVs, the detailed results, a summary and the per-condition decision (Bonferroni-corrected) to the `muestra/` folder, which is not committed:

```bash
python -m scripts.generar_muestra --repeticiones 30 --salida muestra
```

## Docker and Google Cloud Run

```bash
docker build -t qrypta .
docker run --rm -p 8080:8080 -e QRYPTA_HMAC_KEY="<key>" qrypta
```

The app is then available at `http://localhost:8080`. To deploy to Cloud Run, copy `env.yaml.ejemplo` to `env.yaml` (it is in `.gitignore`), replace the key value and run:

```bash
gcloud run deploy qrypta --source . --region <region> --allow-unauthenticated --env-vars-file env.yaml
```

`politica_limpieza.json` keeps the two most recent images in Artifact Registry and deletes the rest:

```bash
gcloud artifacts repositories set-cleanup-policies <repository> --location <region> --policy politica_limpieza.json
```

The HMAC key never goes into the image or the repository.

## Authors

| Member | Modules |
|---|---|
| Larissa Aiko Kian | M1, M2, M3, M8 |
| Anthony Ojeda | M4, M5, M6, M7 |

Universidad Columbia del Paraguay · Computer Engineering · San Lorenzo campus · 2026

## License

Copyright © 2026 Larissa Aiko Kian and Anthony Ojeda. **All rights reserved.** The code is published for academic review and evaluation; to reuse it, please contact the authors. See [LICENSE](LICENSE).

Third-party dependencies keep their own licenses (Python: PSF; Qiskit, Streamlit and Docker: Apache 2.0; Scikit-Learn, NumPy, SciPy and pandas: BSD; Plotly: MIT; Matplotlib: PSF-compatible license; fpdf2: LGPL 3.0).
