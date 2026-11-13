import os
os.environ.setdefault("QRYPTA_HMAC_KEY", "clave-solo-para-pruebas")
from streamlit.testing.v1 import AppTest
from core import prng

def test_flujo_completo():
    at = AppTest.from_file("../app/main.py", default_timeout=120).run()
    assert not at.exception
    at.switch_page("vistas/laboratorio.py").run()
    at.selectbox[1].select(128).run()                       # longitud de clave
    at.text_input[0].input("Gato Azul").run()               # semilla escrita como texto
    at.button[0].click().run()
    conf = at.session_state["experimento"]["config"]
    assert not at.exception and conf["longitud_clave"] == 128
    assert conf["semilla_origen"] == "texto" and conf["semilla"] == prng.interpretar_semilla("gato azul")[0]
    at.switch_page("vistas/analisis.py").run(); assert not at.exception
    at.switch_page("vistas/clasificacion.py").run()
    at.button[0].click().run(); assert not at.exception
    assert "mejor_modelo" in at.session_state["experimento"]["ml"]
    at.button[1].click().run(); assert not at.exception      # serie por volumen
    assert len(at.session_state["serie"]) == 12
    at.switch_page("vistas/dashboard.py").run()
    at.button[0].click().run(); assert not at.exception
    codigo = at.session_state["exportacion"]["codigo"]
    at.switch_page("vistas/verificar.py").run()
    at.text_input[0].input(codigo).run()
    at.button[0].click().run()
    assert not at.exception
    assert any("VÁLIDO" in s.value for s in at.success)

def test_vistas_sin_experimento_avisan():
    at = AppTest.from_file("../app/main.py").run()
    for v in ("analisis", "clasificacion", "dashboard"):
        at.switch_page(f"vistas/{v}.py").run()
        assert not at.exception and len(at.warning) == 1

def test_interpretaciones_didacticas():
    from app import didactica as dd
    from core import experimento
    exp = experimento.ejecutar(1000, 256, 20260101)
    est, ml = exp["estadistica"], exp["ml"]
    import numpy as np
    for texto in (dd.interpretar_bytes(np.packbits(exp["secuencias"]["PRNG"]), "PRNG"), dd.interpretar_entropia(est),
                  dd.interpretar_pruebas(est), dd.interpretar_autocorrelacion(est), dd.interpretar_clasificacion(ml),
                  dd.interpretar_matriz("Random Forest", ml["resultados"]["Random Forest"]),
                  dd.interpretar_serie(experimento.serie_por_volumen(64, 3, volumenes=(100, 1000)))):
        assert isinstance(texto, str) and len(texto) > 80
    assert dd.num(1234.5, 1) == "1.234,5" and dd.pct(0.5) == "50,0 %"
    sesgada = (np.random.default_rng(0).random(80_000) < 0.7).astype(np.uint8)
    assert "no pasa" in dd.interpretar_pruebas({"PRNG": est["PRNG"], "QRNG": experimento.estadistica.analizar(sesgada)})
