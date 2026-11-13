import os
import numpy as np
os.environ.setdefault("QRYPTA_HMAC_KEY", "clave-solo-para-pruebas")
from core import prng, qrng, estadistica as est, ml, experimento, informe, verificacion

def test_prng_reproducible_y_mt():
    assert np.array_equal(prng.generar_bits_prng(1000, 42), prng.generar_bits_prng(1000, 42))
    assert not np.array_equal(prng.generar_bits_prng(1000, 42), prng.generar_bits_prng(1000, 43))
    import random; assert random.Random(1).getstate()[0] == 3        # MT19937 en CPython

def test_qrng_balance_y_orden():
    b = qrng.generar_bits_qrng(16_000)
    assert len(b) == 16_000 and set(np.unique(b)) <= {0, 1}
    assert abs(b.mean() - 0.5) < 3 * np.sqrt(0.25 / 16_000)

def test_nist_vectores_documentados():
    # Ejemplos de NIST SP 800-22 Rev. 1a, secciones 2.1.8 y 2.3.8
    assert round(est.monobit(np.array([int(c) for c in "1011010101"])), 6) == 0.527089
    assert round(est.runs(np.array([int(c) for c in "1001101011"])), 6) == 0.147232

def test_entropia_esperada_observada_diferencia():
    a = est.analizar(np.array([0, 1] * 512, dtype=np.uint8))
    assert a["entropia_esperada"] == 1.0 and a["entropia_observada"] == 1.0 and a["entropia_diferencia"] == 0.0
    assert est.entropia_shannon(np.zeros(100, dtype=np.uint8)) == 0.0

def test_monobit_detecta_sesgo():
    sesgada = (np.random.default_rng(0).random(10_000) < 0.9).astype(np.uint8)
    assert est.monobit(sesgada) < 0.01

def test_indicadores_por_clave():
    claves = np.array([[0, 0, 0, 0, 1, 1, 1, 1] * 8, [0, 1] * 32], dtype=np.uint8)
    ind = est.indicadores_por_clave(claves)
    assert ind.shape == (2, len(est.NOMBRES_INDICADORES))
    assert ind[0, 0] == 0.5 and ind[0, 2] == 16 and ind[0, 3] == 4      # frecuencia, rachas, racha máxima
    assert ind[1, 2] == 64 and ind[1, 3] == 1 and ind[1, 4] == -1.0     # alternancia: autocorrelación lag 1 = -1

def test_clasificacion_control_positivo():
    # Generador deliberadamente débil (80 % de unos) frente al QRNG: los modelos deben distinguirlos.
    debil = (np.random.default_rng(1).random((500, 256)) < 0.8).astype(np.uint8)
    r = ml.entrenar_y_evaluar(debil, qrng.generar_bits_qrng(500 * 256).reshape(500, 256))
    m = r["resultados"][r["mejor_modelo"]]
    assert m["accuracy"] > 0.95 and m["sensibilidad"] > 0.95 and m["especificidad"] > 0.95 and m["p_valor_vs_azar"] < 0.01

def test_experimento_completo_y_metricas_coherentes():
    exp = experimento.ejecutar(1000, 256, 20260101)
    assert exp["secuencias"]["PRNG"].shape == exp["secuencias"]["QRNG"].shape == (256_000,)
    assert exp["ml"]["n_entrenamiento"] == 1400 and exp["ml"]["n_prueba"] == 600
    for m in exp["ml"]["resultados"].values():
        (vn, fp), (fn, vp) = m["matriz_confusion"]
        assert vn + fp == 300 and fn + vp == 300
        assert abs(m["accuracy"] - (vp + vn) / 600) < 1e-9 and abs(m["accuracy"] + m["tasa_error"] - 1) < 1e-9
        assert 0.40 < m["accuracy"] < 0.60                          # MT19937 y QRNG simulado: cerca del azar

def test_longitudes_y_reproducibilidad():
    for longitud in (64, 128, 256):
        exp = experimento.generar(100, longitud, 7)
        assert experimento.claves(exp, "PRNG").shape == (100, longitud)
    assert np.array_equal(experimento.generar(100, 64, 7)["secuencias"]["PRNG"], experimento.generar(100, 64, 7)["secuencias"]["PRNG"])

def test_informe_csv_verificable_con_conclusion():
    exp = experimento.ejecutar(100, 128, 5)
    csv1, csv2 = informe.exportar_csv(exp), informe.exportar_csv(exp)
    cod1, cont1, conf = verificacion.leer_csv(csv1); cod2, _, _ = verificacion.leer_csv(csv2)
    assert cod1 != cod2 and cod1.split("-")[3] == cod2.split("-")[3]      # códigos distintos, misma huella
    assert conf["semilla_prng"] == "5" and conf["cantidad_claves"] == "100" and conf["longitud_clave"] == "128"
    assert verificacion.verificar_codigo(cod1, cont1)["integro"] is True
    assert "modelos,particion," in csv1 and "modelos,Random Forest_parametros,n_estimators=100" in csv1
    assert "conclusion,texto," in csv1 and informe.conclusion(exp).startswith(("Ambos", "No superó"))

def test_serie_por_volumen():
    filas = experimento.serie_por_volumen(64, 11, volumenes=(100, 1000))
    assert len(filas) == 8 and {f["n_claves"] for f in filas} == {100, 1000}

def test_semilla_numero_o_texto():
    assert prng.interpretar_semilla("20260101") == (20260101, "numero")
    s1, origen = prng.interpretar_semilla("Gato  Azul ")
    assert origen == "texto" and 0 <= s1 <= prng.SEMILLA_MAX
    assert prng.interpretar_semilla("gato azul")[0] == s1                  # normalización: mismo texto, misma semilla
    assert prng.interpretar_semilla("gato azul!")[0] != s1
    for invalida in ("", "   ", "4294967296", "x" * 33):
        try:
            prng.interpretar_semilla(invalida); assert False
        except ValueError:
            pass

def test_qrng_en_hilos_como_streamlit():
    # Streamlit importa y ejecuta cada vista en hilos distintos. Qiskit 2.5.x se cae (segmentation fault) si se importa
    # en un hilo que termina y se usa en otro; por eso requirements.txt fija qiskit 2.4.2. Se prueba en un proceso aparte.
    import subprocess, sys, textwrap
    codigo = textwrap.dedent("""
        import threading
        def importar():
            import core.qrng
        t = threading.Thread(target=importar); t.start(); t.join()
        def usar():
            import core.qrng
            assert len(core.qrng.generar_bits_qrng(64)) == 64
        t = threading.Thread(target=usar); t.start(); t.join()
        print("ok")
    """)
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, timeout=120,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr[-500:]

def test_qrng_respeta_las_probabilidades_del_circuito():
    # El sorteo sigue lo que calcula Qiskit: con RY(θ), P(1) = sen²(θ/2) = 0,7
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(1); qc.ry(2 * np.arcsin(np.sqrt(0.7)), 0)
    b = qrng.generar_bits_circuito(qc, 40_000)
    assert abs(b.mean() - 0.7) < 4 * np.sqrt(0.21 / 40_000)

def test_qrng_sin_semilla_lotes_distintos():
    assert not np.array_equal(qrng.generar_bits_qrng(256), qrng.generar_bits_qrng(256))

def test_berlekamp_massey_vectores_conocidos():
    assert est.berlekamp_massey(np.zeros(50, dtype=np.uint8)) == 0
    assert est.berlekamp_massey(np.array([0, 0, 0, 1], dtype=np.uint8)) == 4
    lfsr = np.zeros(2000, dtype=np.uint8); lfsr[:17] = 1
    for i in range(17, len(lfsr)):
        lfsr[i] = lfsr[i - 17] ^ lfsr[i - 14]
    assert est.berlekamp_massey(lfsr) == 17

def test_p_complejidad_exacto_frente_a_fuerza_bruta():
    import itertools
    n = 10
    cuenta = np.zeros(n + 1)
    for t in itertools.product((0, 1), repeat=n):
        cuenta[est.berlekamp_massey(np.array(t, dtype=np.uint8))] += 1
    acumulada = np.cumsum(cuenta) / 2 ** n
    assert all(abs(acumulada[L] - est.p_complejidad_lineal(L, n)) < 1e-12 for L in range(n + 1))

def test_complejidad_lineal_separa_mt19937_de_fuente_ideal():
    # 6.000 claves de 256 bits -> 48.000 bits analizados (1 de cada 32): más que 2 × 19.937
    exp = experimento.analizar(experimento.generar(6000, 256, 20260101))
    p, q = exp["estadistica"]["PRNG"], exp["estadistica"]["QRNG"]
    assert p["alcanza_grado_mt"] and p["complejidad_lineal"] == 19937 and not p["aprueba_complejidad"]
    assert abs(q["complejidad_lineal"] - 24000) <= 10 and q["aprueba_complejidad"]
    # el QRNG simulado tampoco tiene estructura en la secuencia completa (con el muestreo de Aer daba 19.937)
    assert abs(est.berlekamp_massey(exp["secuencias"]["QRNG"][:44_000]) - 22_000) <= 10

def test_complejidad_en_informe_y_conclusion():
    exp = experimento.ejecutar(100, 256, 5)
    csv = informe.exportar_csv(exp)
    assert "estadistica,PRNG_complejidad_lineal," in csv and "config,muestreo_qrng," in csv
    assert "Complejidad lineal" in informe.conclusion(exp) and "se requieren" in informe.conclusion(exp)
