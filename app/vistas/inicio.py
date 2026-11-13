import streamlit as st

st.title("QRYPTA — Simulador de aleatoriedad clásica y cuántica")
st.markdown("#### Un laboratorio para entender qué hace que una clave sea «buena»")

st.markdown("""
Toda la seguridad de un sistema cifrado descansa en una idea simple: **nadie debe poder adivinar la clave**.
Para eso, las claves se fabrican con generadores de números aleatorios. Pero no todos los generadores son iguales:

- Un generador **clásico (PRNG)** es un algoritmo: a partir de un número inicial, la *semilla*, calcula una secuencia
  que *parece* aleatoria. Con la misma semilla, produce siempre la misma secuencia.
- Un generador **cuántico (QRNG)** obtiene sus bits midiendo partículas en superposición, un fenómeno que, según la física,
  es impredecible. En este simulador se usa una **simulación** por software de ese proceso.

**La pregunta del experimento:** si se generan muchas claves con cada uno, ¿se puede notar la diferencia?
Usted lo va a comprobar con pruebas estadísticas y con cuatro modelos de Inteligencia Artificial.
""")

st.subheader("El recorrido")
c = st.columns(4)
pasos = [("2. Laboratorio", "Genera claves con ambos generadores y las observa en gráficos.", "Qué es una semilla, un bit y un byte."),
         ("3. Análisis", "Mide entropía, equilibrio, rachas, autocorrelación y complejidad lineal.", "Qué es la entropía y cómo se lee un p-valor."),
         ("4. Clasificación con IA", "Entrena cuatro modelos para que adivinen de qué generador salió cada clave.", "Cómo se evalúa un clasificador."),
         ("5. Dashboard e Informe", "Reúne los resultados y exporta un informe con código de verificación.", "Cómo comunicar un resultado experimental.")]
for col, (titulo, hace, aprende) in zip(c, pasos):
    with col.container(border=True):
        st.markdown(f"**{titulo}**")
        st.write(hace)
        st.caption(f"Aprende: {aprende}")
st.caption("La vista 6 permite verificar un informe exportado, propio o de otra persona.")

st.subheader("Antes de empezar")
st.markdown("""
- No necesita cuenta ni inicio de sesión.
- Sus datos viven solo en esta pestaña: **si la cierra o recarga, el experimento se pierde**. Exporte el informe antes.
- Si su docente le asignó una **semilla** (un número o una palabra), ingrésela en el Laboratorio antes de generar.
- Para entregar un informe, descargue el **CSV** y no lo abra ni lo guarde con Excel: cambiaría su contenido.
""")
st.warning("Detectar una diferencia estadística entre generadores **no** significa «romper» una clave. "
           "Este simulador estudia la detección de patrones, no ataques criptográficos.", icon=":material/info:")

st.subheader("Conceptos clave")
TEMAS = {
    "Bits, bytes y claves": """
Una **clave** es una secuencia de bits. Una clave de 256 bits tiene 2²⁵⁶ valores posibles, un número de 78 cifras:
probarlos todos es imposible. Pero eso solo protege si **todos los valores son igual de probables**; si el generador
prefiere algunos, el espacio real de búsqueda se achica.

Para mostrarla se usa el **hexadecimal**: cada cifra (0–9, a–f) representa 4 bits. `1011 0010` se escribe `b2`.
Un **byte** son 8 bits, es decir, un número de 0 a 255.""",
    "Generador clásico (PRNG) y semilla": """
El **Mersenne Twister (MT19937)** es el generador por defecto de Python (`random`). Es rápido y estadísticamente muy bueno,
pero es **determinista**: la misma semilla produce la misma secuencia, y observando 624 salidas consecutivas se puede
reconstruir su estado interno. Por eso no está aprobado para criptografía; para claves reales Python ofrece `secrets`.

La **semilla** es el punto de partida. En el Laboratorio puede escribir un número o un texto corto: el texto se convierte
en número con la función hash SHA-256. Así, el mismo texto siempre da la misma semilla.""",
    "Generador cuántico simulado (QRNG)": """
Un **qubit** puede estar en superposición de 0 y 1. La compuerta **Hadamard** lo deja con 50 % de probabilidad de cada
resultado, y al medirlo se obtiene un bit. Este simulador usa **Qiskit** para calcular el estado del circuito y sus
probabilidades, y sortea cada medición con el generador criptográfico del sistema operativo, alimentado por entropía física.
No usa hardware cuántico: es un **modelo de fuente cuántica ideal**, por eso se habla de **QRNG simulado**.

¿Por qué no se usa el sorteo de Qiskit Aer? Porque Aer sortea las mediciones con un Mersenne Twister interno: su salida
tendría la misma estructura que el generador clásico, y se estaría comparando un Mersenne Twister consigo mismo.""",
    "Complejidad lineal": """
Mide la **regla lineal más corta** capaz de generar una secuencia. En una fuente ideal no hay atajo: la regla necesita la mitad
de los bits. En un algoritmo determinista como el Mersenne Twister, la complejidad se detiene en el tamaño de su estado
(19.937 bits), por más datos que se analicen. Es una forma de ver que **pasar las pruebas estadísticas no es lo mismo que ser
imprevisible**. Para verlo hacen falta muchos bits: use 10.000 claves de 256 bits.""",
    "Entropía": """
Mide la **incertidumbre** de una fuente. Una moneda perfecta tiene 1 bit de entropía por lanzamiento: el máximo.
Una moneda que sale cara el 90 % de las veces tiene solo 0,47: es más fácil de adivinar.""",
    "Pruebas estadísticas y p-valor": """
Una prueba estadística parte de suponer que la fuente es perfecta y calcula el **p-valor**: la probabilidad de ver un
resultado así de raro si esa suposición fuera cierta. Si p < 0,01, el resultado es demasiado raro y se sospecha un defecto.
Ojo: incluso una fuente perfecta da p < 0,01 en 1 de cada 100 pruebas.""",
    "Inteligencia Artificial como instrumento": """
Un **clasificador** aprende a separar ejemplos en categorías. Aquí cada clave se resume en 12 números (sus indicadores
estadísticos) y la categoría es su origen: PRNG o QRNG. Se entrena con el 70 % de las claves y se evalúa con el 30 %
restante, que el modelo nunca vio. Si acierta alrededor del 50 %, está adivinando: no encontró diferencias.""",
}
for titulo, texto in TEMAS.items():
    with st.expander(titulo):
        st.markdown(texto)

st.subheader("Ponga a prueba su intuición")
st.caption("Tres preguntas rápidas. Vuelva a responderlas al terminar el recorrido.")
PREGUNTAS = [
    ("Si genera claves dos veces con el PRNG y la misma semilla, ¿qué obtiene?",
     ["Las mismas claves", "Claves distintas", "Depende del momento"], 0,
     "Un PRNG es un algoritmo determinista: la misma semilla produce exactamente la misma secuencia. Lo comprobará en el Laboratorio."),
    ("Una secuencia 0101 0101 0101… ¿tiene entropía alta o baja?",
     ["Alta (1 bit por bit)", "Baja (cercana a 0)"], 0,
     "Tiene la misma cantidad de ceros que de unos, así que su entropía es máxima. Sin embargo, es totalmente predecible: "
     "por eso la entropía sola no alcanza y se usan otras pruebas, como la de rachas."),
    ("Un modelo de IA acierta el origen del 51 % de las claves de prueba. ¿Qué significa?",
     ["Distingue los generadores", "Probablemente está adivinando"], 1,
     "Con dos clases en igual cantidad, adivinar da 50 %. Un 51 % puede aparecer por azar; por eso se calcula el p-valor."),
]
for i, (pregunta, opciones, correcta, explicacion) in enumerate(PREGUNTAS):
    r = st.radio(pregunta, opciones, index=None, key=f"quiz_{i}")
    if r is not None:
        (st.success if opciones.index(r) == correcta else st.error)(
            ("Correcto. " if opciones.index(r) == correcta else "No exactamente. ") + explicacion)

st.divider()
st.page_link("vistas/laboratorio.py", label="Comenzar: 2. Laboratorio de Generación de Claves", icon=":material/arrow_forward:")
