# QRYPTA

**An educational web platform that compares the randomness of classical (PRNG) and simulated quantum (QRNG) generators, and their vulnerability to Artificial Intelligence attacks.**

![Status](https://img.shields.io/badge/status-in%20development-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![License](https://img.shields.io/badge/license-all%20rights%20reserved-lightgrey)

[🇪🇸 Español](README.md) · 🇬🇧 English

---

## Overview

QRYPTA is a public, interactive web simulator aimed at Computer Engineering students at Universidad Columbia del Paraguay (San Lorenzo campus). Users can generate a classical cryptographic key (PRNG) and a simulated quantum key (QRNG), run both through statistical randomness tests, and launch a machine-learning prediction attack against them, showing experimentally how differently the two paradigms hold up.

The project is the practical component of a 2026 undergraduate capstone thesis (TCC).

> **Educational scope.** The adversarial demonstration is a bounded, didactic simulation. It is not a validated cryptanalysis of a production cryptographic system.

## What it does

1. **Generates** bit sequences with a classical PRNG (Mersenne Twister, MT19937) and a simulated QRNG (Hadamard-gate circuits in Qiskit).
2. **Measures** randomness with Shannon entropy, bit frequency, autocorrelation and NIST Statistical Test Suite tests (Monobit, Runs).
3. **Attacks** both sources with four Scikit-Learn classifiers (Decision Tree, Random Forest, linear SVM and a multilayer neural network) and simulates recovering an XOR-encrypted message (ciphertext-only and known-plaintext).
4. **Displays** results in an interactive Plotly dashboard and exports a PDF or CSV report signed with HMAC-SHA256.
5. **Verifies**, from a teacher-facing page, the authenticity of a received report without storing any data from the original session.

## Modules

| Axis | Module | Description |
|---|---|---|
| A. Cryptographic engine | M1 | Classical pseudorandom generator (Mersenne Twister, configurable seeds, XOR cipher) |
| | M2 | Quantum randomness simulator (Qiskit, Hadamard gates, `shots` parameter) |
| | M3 | Entropy and randomness tests (Shannon, NIST) |
| B. AI and cryptanalysis | M4 | Adversarial machine learning (Scikit-Learn, 70 % train / 30 % test) |
| | M5 | Adversarial agent and attack vectors on XOR encryption |
| | M6 | Analytics dashboard and vulnerability metrics, with signed reports |
| C. Web and infrastructure | M7 | Educational web interface (Streamlit) and teacher verification |
| | M8 | Containerization (Docker) and serverless deployment (Google Cloud Run) |

## Experiment variables

- **IV₁, classical generator:** Mersenne Twister (MT19937), used as the baseline.
- **IV₂, quantum generator:** Hadamard circuits on qubits in superposition, simulated in Qiskit.
- **DV, cryptographic vulnerability:** Shannon entropy, NIST tests and the accuracy of the AI models.

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Quantum simulation | IBM Qiskit |
| Web interface | Streamlit |
| Artificial intelligence | Scikit-Learn |
| Data | pandas, NumPy |
| Visualization | Plotly |
| Report verification | HMAC-SHA256 (Python `hmac` module) |
| Containers | Docker |
| Cloud | Google Cloud Run |

The architecture is **stateless**: there is no database and state lives in `st.session_state`. This gives privacy by design, since no personal data is recorded between sessions.

## Running locally

> The project is under development. The commands below assume a typical Streamlit app layout and may change.

```bash
git clone https://github.com/qryptateam-dev/qrypta-system.git
cd qrypta-system
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If you use report signing, set the secret key in a local `.env` file (never commit it).

## Docker and Google Cloud Run

```bash
docker build -t qrypta .
docker run --rm -p 8080:8080 qrypta
```

The app is then available at `http://localhost:8080`. To deploy to Google Cloud Run (requires a configured `gcloud`):

```bash
gcloud run deploy qrypta --source . --region <region> --allow-unauthenticated
```

The HMAC key and any other secret are passed as service environment variables, never baked into the image.

## Authors

| Member | Modules |
|---|---|
| Larissa Aiko Kian | M1, M2, M3, M8 |
| Anthony Ojeda | M4, M5, M6, M7 |

Universidad Columbia del Paraguay · Computer Engineering · San Lorenzo campus · 2026

## License

Copyright © 2026 Larissa Aiko Kian and Anthony Ojeda. **All rights reserved.** The code is published for academic review and evaluation; contact the authors to request permission to reuse it. See [LICENSE](LICENSE).

Third-party dependencies keep their own licenses (Python: PSF; Qiskit, Streamlit and Docker: Apache 2.0; Scikit-Learn: BSD 3-Clause).
