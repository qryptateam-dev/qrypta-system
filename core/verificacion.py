"""
QRYPTA — Código de verificación por exportación y verificación en lote
(CU-11, CU-12 y CU-17).

Sin base de datos, sin perfiles y sin inicio de sesión:
- Aleatoria:  nonce de 128 bits del CSPRNG del sistema operativo (secrets).
- Única:      dos exportaciones nunca comparten nonce en la práctica.
- Verificable: HMAC-SHA256 con la clave de la variable de entorno
              QRYPTA_HMAC_KEY. Se verifica recalculando, no consultando.
- En lote:    los archivos se procesan en memoria y se descartan; nada se guarda.

Formato de entrega (CSV v1):
  Línea 1:     # QRYPTA-CODIGO,<código>
  Resto:       contenido canónico "seccion,campo,valor" (incluye la semilla).
  La huella SHA-256 se calcula sobre el contenido canónico (todo salvo la línea 1).
"""
import csv
import hashlib
import hmac
import io
import os
import secrets
from collections import defaultdict
from datetime import datetime, timezone

VERSION = "QRY1"
_DOMINIO = b"QRYPTA|v1|"
_CABECERA = "# QRYPTA-CODIGO,"
MAX_ARCHIVOS_LOTE = 50              # valores propuestos, configurables
MAX_BYTES_ARCHIVO = 2 * 1024 * 1024


# ---------- núcleo del código ----------
def _clave() -> bytes:
    clave = os.environ.get("QRYPTA_HMAC_KEY")
    if not clave:
        raise RuntimeError("Falta la variable de entorno QRYPTA_HMAC_KEY")
    return clave.encode("utf-8")


def _canon(contenido: str) -> str:
    return contenido.replace("\r\n", "\n").strip()


def _h16(contenido: str) -> str:
    return hashlib.sha256(_canon(contenido).encode("utf-8")).hexdigest()[:16]


def _tag(nonce: str, ts: str, h16: str) -> str:
    msg = _DOMINIO + f"{nonce}|{ts}|{h16}".encode("ascii")
    return hmac.new(_clave(), msg, hashlib.sha256).hexdigest()[:32]


def generar_codigo(contenido: str) -> str:
    nonce = secrets.token_hex(16)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    h16 = _h16(contenido)
    return f"{VERSION}-{nonce}-{ts}-{h16}-{_tag(nonce, ts, h16)}"


def verificar_codigo(codigo: str, contenido: str | None = None) -> dict:
    """CU-12: verificación individual (código solo, o código + contenido)."""
    try:
        version, nonce, ts, h16, tag = codigo.strip().split("-")
    except ValueError:
        return {"valido": False, "motivo": "Formato de código incorrecto"}
    if version != VERSION:
        return {"valido": False, "motivo": "Versión de código desconocida"}
    if not hmac.compare_digest(tag, _tag(nonce, ts, h16)):
        return {"valido": False, "motivo": "El código no fue emitido por QRYPTA"}
    r = {"valido": True, "emitido_utc": ts, "id_exportacion": nonce[:8], "nonce": nonce, "h16": h16}
    if contenido is not None:
        r["integro"] = hmac.compare_digest(h16, _h16(contenido))
    return r


# ---------- formato de entrega (CU-11) ----------
def construir_csv(semilla_prng: int, cantidad_claves: int, filas: list[tuple[str, str, str]]) -> str:
    """Arma el CSV exportable: línea de código + contenido canónico."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["seccion", "campo", "valor"])
    w.writerow(["config", "formato", "1"])
    w.writerow(["config", "semilla_prng", str(semilla_prng)])
    w.writerow(["config", "cantidad_claves", str(cantidad_claves)])
    for fila in filas:
        w.writerow(fila)
    contenido = _canon(buf.getvalue())
    return f"{_CABECERA}{generar_codigo(contenido)}\n{contenido}\n"


def leer_csv(texto: str) -> tuple[str | None, str, dict]:
    """Separa la línea del código, el contenido canónico y los campos de configuración."""
    texto = texto.replace("\r\n", "\n")
    primera, _, resto = texto.partition("\n")
    codigo = primera[len(_CABECERA):].strip() if primera.startswith(_CABECERA) else None
    config = {}
    for fila in csv.reader(io.StringIO(resto)):
        if len(fila) == 3 and fila[0] == "config":
            config[fila[1]] = fila[2]
    return codigo, resto, config


# ---------- verificación en lote (CU-17) ----------
def _fecha(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)


def verificar_lote(archivos: dict[str, bytes],
                   desde: datetime | None = None,
                   hasta: datetime | None = None,
                   semillas_asignadas: dict[str, str] | None = None) -> list[dict]:
    """
    archivos:           {nombre_de_archivo: bytes del CSV}
    desde / hasta:      ventana de entrega (UTC), opcional
    semillas_asignadas: {semilla: identificador del alumno}, opcional
    Devuelve una fila por archivo con su estado y alertas. No guarda nada.
    """
    if len(archivos) > MAX_ARCHIVOS_LOTE:
        raise ValueError(f"Máximo {MAX_ARCHIVOS_LOTE} archivos por lote")
    filas = []
    for nombre, datos in archivos.items():
        f = {"archivo": nombre, "valido": False, "integro": False, "emitido_utc": "",
             "semilla": "", "alumno_asignado": "", "alertas": []}
        if len(datos) > MAX_BYTES_ARCHIVO:
            f["alertas"].append("Archivo demasiado grande")
            filas.append(f); continue
        try:
            codigo, contenido, config = leer_csv(datos.decode("utf-8"))
        except UnicodeDecodeError:
            f["alertas"].append("No es un CSV de texto (¿se entregó el PDF?)")
            filas.append(f); continue
        if not codigo:
            f["alertas"].append("Sin código QRYPTA en la primera línea")
            filas.append(f); continue
        r = verificar_codigo(codigo, contenido)
        f["semilla"] = config.get("semilla_prng", "")
        if not r["valido"]:
            f["alertas"].append(r["motivo"])
            filas.append(f); continue
        f.update(valido=True, integro=r["integro"], emitido_utc=r["emitido_utc"],
                 _nonce=r["nonce"], _h16=r["h16"])
        if not r["integro"]:
            f["alertas"].append("Contenido modificado después de la exportación")
        if (desde and _fecha(r["emitido_utc"]) < desde) or (hasta and _fecha(r["emitido_utc"]) > hasta):
            f["alertas"].append("Emitido fuera de la ventana de entrega")
        if semillas_asignadas is not None:
            if f["semilla"] in semillas_asignadas:
                f["alumno_asignado"] = semillas_asignadas[f["semilla"]]
            else:
                f["alertas"].append("Semilla no asignada a ningún alumno")
        filas.append(f)

    # Cruces entre archivos del mismo lote
    por_nonce, por_h16, por_semilla = defaultdict(list), defaultdict(list), defaultdict(list)
    for f in filas:
        if f["valido"]:
            por_nonce[f["_nonce"]].append(f["archivo"])
            por_h16[f["_h16"]].append(f["archivo"])
            if f["semilla"]:
                por_semilla[f["semilla"]].append(f["archivo"])
    for f in filas:
        if not f["valido"]:
            continue
        mismos_archivo = [a for a in por_nonce[f["_nonce"]] if a != f["archivo"]]
        mismo_experimento = [a for a in por_h16[f["_h16"]] if a != f["archivo"] and a not in mismos_archivo]
        misma_semilla = [a for a in por_semilla.get(f["semilla"], []) if a != f["archivo"]
                         and a not in mismos_archivo and a not in mismo_experimento]
        if mismos_archivo:
            f["alertas"].append("Mismo archivo que: " + ", ".join(mismos_archivo))
        if mismo_experimento:
            f["alertas"].append("Mismo experimento reexportado que: " + ", ".join(mismo_experimento))
        if misma_semilla:
            f["alertas"].append("Misma semilla que: " + ", ".join(misma_semilla))
    for f in filas:
        f.pop("_nonce", None); f.pop("_h16", None)
        f["estado"] = "OK" if f["valido"] and not f["alertas"] else ("REVISAR" if f["valido"] else "RECHAZADO")
    return filas


if __name__ == "__main__":
    os.environ.setdefault("QRYPTA_HMAC_KEY", "clave-de-prueba-solo-local")

    def experimento(semilla):  # simula un experimento: la secuencia QRNG cambia siempre
        return [("metrica", "PRNG_accuracy", "0.71"), ("metrica", "QRNG_accuracy", "0.50"),
                ("secuencia", "QRNG_hex", secrets.token_hex(32))]

    ana = construir_csv(111111, 1000, experimento(111111))
    beto_copia = ana                                             # recibe el archivo de Ana
    _, cont_ana, _ = leer_csv(ana)                               # Ana reexporta el mismo análisis
    carla_reexp = f"{_CABECERA}{generar_codigo(_canon(cont_ana))}\n{_canon(cont_ana)}\n"
    diego_editado = construir_csv(444444, 1000, experimento(444444)).replace("0.71", "0.99")
    eva_ok = construir_csv(555555, 1000, experimento(555555))
    fede_semilla_ajena = construir_csv(555555, 1000, experimento(555555))

    lote = {"ana.csv": ana.encode(), "beto.csv": beto_copia.encode(), "carla.csv": carla_reexp.encode(),
            "diego.csv": diego_editado.encode(), "eva.csv": eva_ok.encode(),
            "fede.csv": fede_semilla_ajena.encode(), "gabi.pdf": b"%PDF-1.7\x00\xff binario"}
    asignadas = {"111111": "Ana", "222222": "Beto", "333333": "Carla", "444444": "Diego",
                 "555555": "Eva", "666666": "Fede"}
    for f in verificar_lote(lote, semillas_asignadas=asignadas):
        print(f"{f['archivo']:10} {f['estado']:9} semilla={f['semilla']:7} asignada_a={f['alumno_asignado']:6} {f['alertas']}")
