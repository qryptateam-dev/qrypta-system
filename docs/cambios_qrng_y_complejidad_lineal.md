# Cambios: QRNG simulado como fuente ideal y complejidad lineal

Resumen de los cambios del simulador y de su impacto en el anteproyecto (Anteproyecto_TCC_v6). Las páginas son las del índice del anteproyecto.

> **Antes de modificar el anteproyecto, conviene revisar estos cambios con el tutor:** afectan el Módulo 2, amplían el objetivo específico d) y tocan el Alcance Tentativo.

---

## 1. Motivo

### 1.1 Hallazgo

El QRNG simulado con Qiskit Aer **no era una fuente distinta del PRNG**. Aer sortea cada medición con un Mersenne Twister interno (`mt19937_64`, clase `RngEngine` de su código fuente). Se comprobó con la complejidad lineal (algoritmo de Berlekamp-Massey) sobre 44.000 bits:

| Fuente | Complejidad lineal | Esperada en una fuente ideal |
|---|---|---|
| QRNG simulado con muestreo de Qiskit Aer (1 o 16 qubits) | **19.937** | ≈ 22.000 |
| MT19937 de Python (un bit por palabra de 32 bits) | **19.937** | ≈ 22.000 |
| `os.urandom` (sistema operativo) | 22.000 | ≈ 22.000 |
| Control: LFSR de grado 17 | 17 | — |

19.937 es el grado de la recurrencia del Mersenne Twister. Con el diseño anterior, el experimento comparaba **un Mersenne Twister contra otro**. Por eso ni las pruebas estadísticas ni los modelos de IA podían encontrar diferencias.

El anteproyecto ya advertía (p. 27–28) que el muestreo de un simulador cuántico "se realiza con un generador pseudoaleatorio interno". Este hallazgo lo cuantifica.

### 1.2 Consecuencia

Hacían falta dos cambios:

1. Que el QRNG simulado represente de verdad una **fuente ideal**, como la que promete un QRNG.
2. Que el simulador incluya una medición capaz de mostrar la propiedad que diferencia a un PRNG de una fuente ideal: **su estructura determinista**. Las pruebas de primer orden (Monobit, rachas, autocorrelación) y los indicadores por clave no la detectan.

---

## 2. Cambios en el simulador

### Módulo 2: QRNG simulado (`core/qrng.py`)

| | Antes | Ahora |
|---|---|---|
| Estado y probabilidades del circuito | Qiskit Aer | Qiskit (`quantum_info.Statevector`) |
| Sorteo de cada medición | Mersenne Twister interno de Aer (`mt19937_64`) | `secrets`: generador criptográfico del sistema operativo, alimentado por entropía física |
| Semilla | Interna del simulador | Ninguna |
| Lote reproducible | Con la semilla interna | No: cada lote es irrepetible |
| Estructura lineal | Sí (19.937) | No (≈ mitad de los bits) |

**Cómo funciona:**
- El circuito sigue siendo el mismo: 16 qubits, una compuerta Hadamard por qubit y `shots = ⌈bits / 16⌉`.
- Cada medición se sortea respetando las probabilidades que calcula Qiskit (método de la transformada inversa). Si el circuito cambiara, por ejemplo con una rotación RY que deje un qubit en 70/30, los bits seguirían esa distribución; hay una prueba automática que lo verifica.
- No se usa `Statevector.sample_memory` porque sortea con el PRNG de NumPy (PCG64).
- El informe registra el método de muestreo en el campo `config,muestreo_qrng`.
- Se quitó la dependencia `qiskit-aer`.

### Módulo 3: complejidad lineal (`core/estadistica.py`)

**Qué se agregó:**
- `berlekamp_massey(bits)` calcula la complejidad lineal: la longitud del registro de desplazamiento con realimentación lineal (LFSR) más corto que genera la secuencia (Massey, 1969). Es el algoritmo de la prueba 2.10 del NIST SP 800-22, aplicado a la secuencia completa y no en bloques.
- `p_complejidad_lineal(L, n)` calcula el p-valor exacto: P(complejidad ≤ L) en una fuente ideal de n bits. Usa la cantidad exacta de secuencias con cada complejidad (Rueppel, 1986): 1 si l = 0 y 2^min(2n−2l, 2l−1) si l ≥ 1. Es una prueba unilateral, porque una complejidad baja indica estructura, con α = 0,01. Se verificó contra el conteo por fuerza bruta de las 1.024 secuencias de 10 bits.
- `complejidad_lineal(bits)` analiza **1 de cada 32 bits** (el primero de cada bloque de 32). El MT19937 entrega palabras de 32 bits, y se aplica **el mismo procedimiento a ambos generadores**.

**Volumen necesario:** para revelar una estructura de grado 19.937 hacen falta al menos 39.874 bits analizados, unas 4.985 claves de 256 bits. En el simulador eso corresponde al volumen de **10.000 claves**. Con 100 o 1.000 claves, ambos generadores dan ≈ n/2 y la interfaz lo explica.

**Resultado** (10.000 claves de 256 bits, semilla 20260101, 80.000 bits analizados):

| | PRNG (MT19937) | QRNG simulado |
|---|---|---|
| Complejidad lineal | 19.937 | 40.000 |
| Esperada en una fuente ideal | 40.000 | 40.000 |
| p-valor | < 10⁻³⁰⁰ (no pasa) | 0,67 (pasa) |

Mientras tanto, Monobit, rachas, autocorrelación y los cuatro modelos de IA siguen sin distinguir las fuentes: el mejor modelo llegó a 50,8 % de precisión.

### Módulos 6 y 7: informe, dashboard e interfaz

**Informe CSV y PDF:** incluyen, por generador, los bits analizados, la complejidad lineal y su p-valor. La conclusión automática agrega una frase sobre la complejidad lineal.

**Vistas:**
- **Vista 3 (Análisis):** nueva sección "4. Complejidad lineal", con gráfico, interpretación automática y guía de lectura.
- **Vista 5 (Dashboard):** tres filas nuevas en la comparación: complejidad lineal, semilla (32 bits, como máximo 2³² secuencias posibles, frente a "no usa semilla") y reproducibilidad (misma semilla, mismas claves).
- **Vista 1 (Inicio):** se actualizó el concepto "Generador cuántico simulado" y se agregó el concepto "Complejidad lineal".
- **Vista 4 (Clasificación):** cuando ningún modelo supera al azar, la interpretación explica que los indicadores por clave no capturan una estructura que abarca miles de bits.

**Script de la muestra:** `scripts/generar_muestra.py` agrega `complejidad_lineal` y `p_complejidad` por generador al archivo `resultados_detalle.csv`.

### Verificación

- **Tests:** 22 aprobados (antes 16). Los nuevos cubren:
  - vectores conocidos de Berlekamp-Massey;
  - el p-valor exacto frente a la fuerza bruta;
  - la separación entre MT19937 y la fuente ideal con 6.000 claves;
  - el respeto de las probabilidades del circuito;
  - que los lotes del QRNG no se repiten;
  - la presencia de los campos nuevos en el informe.
- **Tiempo:** un experimento completo con 10.000 claves tarda unos 3 s en una computadora local (criterio de la Tabla 2: 60 s o menos).

---

## 3. Impacto en el anteproyecto

### 3.1 Secciones a actualizar

| Sección (página) | Qué cambia | Texto sugerido |
|---|---|---|
| Delimitación Conceptual (p. 10) | Menciona "QRNG simulado con Qiskit Aer". | "…QRNG simulado con Qiskit, cuyas mediciones se sortean con el generador criptográfico del sistema operativo…" |
| Objetivo específico d) (p. 11) | Agregar la complejidad lineal. | "d) Caracterizar la aleatoriedad de ambas fuentes mediante la entropía, la frecuencia de bits, la autocorrelación, las pruebas Monobit y de rachas del NIST SP 800-22 y la complejidad lineal (algoritmo de Berlekamp-Massey)." |
| Tabla 1, problema 4 (p. 9) | Agregar la complejidad lineal a la solución del Módulo 3. | "…autocorrelación, pruebas Monobit y de rachas, y complejidad lineal." |
| Tabla 2, Criterios de verificación (p. 12–13) | Agregar dos criterios (ver 3.2). | — |
| Relevancia Científica (p. 14) | Reforzar la distinción entre calidad estadística y seguridad. | "La complejidad lineal permite mostrar experimentalmente esa distinción: el Mersenne Twister supera las pruebas habituales y no es distinguido por los modelos de IA, pero su complejidad lineal queda limitada por el tamaño de su estado (19.937)." |
| Computación Cuántica y Generación Cuántica de Números Aleatorios (p. 27–28) | Describir el nuevo muestreo y por qué no se usa Aer. | Ver 3.3. |
| Evaluación Estadística de la Aleatoriedad (p. 28) | Agregar un párrafo sobre la complejidad lineal. | Ver 3.4. |
| Definición de términos: "QRNG simulado" (p. 33) | Hoy dice "con el simulador Qiskit Aer". | "QRNG simulado: modelo por software de una fuente cuántica ideal; en el estudio, Qiskit calcula el estado de un circuito de compuertas de Hadamard y cada medición se sortea con el generador criptográfico del sistema operativo. Imita el comportamiento ideal de la medición cuántica, pero no constituye una fuente cuántica real." |
| Definición de términos (p. 33) | Agregar "Complejidad lineal". | "Complejidad lineal: longitud del registro de desplazamiento con realimentación lineal más corto capaz de generar una secuencia; en una fuente ideal es cercana a la mitad de su longitud (Massey, 1969; Rueppel, 1986)." |
| Alcance de la Interpretación (p. 39) | Aclarar qué mide la complejidad lineal. | "Una complejidad lineal significativamente menor que la esperada indica que la secuencia sigue una regla lineal determinista; no implica que la clave pueda predecirse o reconstruirse en el marco del estudio, que no lo intenta." |
| Descripción de la solución: Módulos 2 y 3 (p. 42) | Reemplazar "ejecutados localmente con el simulador Qiskit Aer" y agregar la complejidad lineal al Módulo 3. | — |
| Tecnologías: Simulación Cuántica (p. 44) | Reemplazar la mención de Aer. | "Qiskit, marco de código abierto de IBM, que modela el circuito cuántico y calcula las probabilidades de medición (módulo `quantum_info`); las mediciones se sortean con el módulo `secrets` de Python, sin cuentas ni servicios cuánticos en la nube." |
| Alcance Tentativo (p. 46) | Hoy excluye "la incorporación de generadores basados en fuentes físicas de aleatoriedad". | Agregar: "El generador criptográfico del sistema operativo se emplea solo como mecanismo de sorteo del QRNG simulado y no constituye un tercer generador del estudio." |
| Referencias (p. 51) | Agregar Massey (1969) y Rueppel (1986), y opcionalmente la documentación de `secrets` y de Qiskit Aer. | Ver 3.5. |

### 3.2 Criterios de verificación sugeridos (Tabla 2)

| Criterio | Procedimiento de verificación | Umbral de aceptación |
|---|---|---|
| Complejidad lineal: algoritmo | Aplicación de Berlekamp-Massey a secuencias de complejidad conocida y comparación del p-valor con el conteo exhaustivo de las secuencias de 10 bits. | LFSR de grado 17: complejidad 17. Secuencia 0001: complejidad 4. p-valor idéntico al conteo exhaustivo (diferencia < 10⁻¹²). |
| QRNG simulado: ausencia de estructura lineal | Complejidad lineal de 44.000 bits consecutivos del QRNG simulado. | Entre 21.990 y 22.010 (n/2 ± 10). |

El criterio actual de proporción de unos del QRNG (entre 0,498 y 0,502) se mantiene sin cambios.

### 3.3 Texto sugerido para la p. 28

> Un simulador cuántico calcula en una computadora clásica las probabilidades del estado cuántico y genera los resultados de la medición mediante muestreo. En Qiskit Aer, ese muestreo se realiza con un Mersenne Twister interno (mt19937_64), de modo que su salida conserva la estructura lineal de ese generador: en pruebas preliminares, la complejidad lineal de sus mediciones fue 19.937, igual a la del MT19937 clásico. Para que el QRNG simulado represente el comportamiento ideal de la medición cuántica, el simulador calcula el estado del circuito y sus probabilidades con Qiskit y sortea cada medición con el generador criptográfico del sistema operativo (módulo secrets de Python), alimentado por entropía física de la máquina. El resultado es un modelo de fuente cuántica ideal —sin semilla, irrepetible y sin estructura lineal—, pero no constituye una fuente de aleatoriedad cuántica real; por esa razón, el documento emplea de forma consistente la expresión «QRNG simulado».

### 3.4 Texto sugerido para la p. 28 (después del párrafo de autocorrelación)

> La complejidad lineal de una secuencia es la longitud del registro de desplazamiento con realimentación lineal más corto capaz de generarla, y se calcula con el algoritmo de Berlekamp-Massey (Massey, 1969), el mismo que emplea la prueba 2.10 del NIST SP 800-22 (Bassham et al., 2010). En una fuente ideal es cercana a la mitad de la longitud de la secuencia; en un generador lineal determinista no supera el tamaño de su estado, por más bits que se analicen. El Mersenne Twister tiene una complejidad lineal máxima de 19.937, por lo que esta medición revela su estructura determinista aun cuando supera las pruebas de primer orden. El simulador la calcula sobre uno de cada 32 bits de cada generador, con un p-valor exacto (Rueppel, 1986), y requiere al menos 39.874 bits analizados —10.000 claves de 256 bits— para que esa estructura sea observable.

### 3.5 Referencias a agregar (verificar formato y DOI)

- Massey, J. L. (1969). Shift-register synthesis and BCH decoding. *IEEE Transactions on Information Theory, 15*(1), 122–127. https://doi.org/10.1109/TIT.1969.1054260
- Rueppel, R. A. (1986). *Analysis and design of stream ciphers*. Springer. https://doi.org/10.1007/978-3-642-82865-2
- Python Software Foundation. (s. f.). *secrets — Generate secure random numbers for managing secrets*. https://docs.python.org/3/library/secrets.html

---

## 4. Limitaciones a declarar

1. **El QRNG simulado no es aleatoriedad cuántica real.** `secrets` es un generador criptográficamente seguro (CSPRNG) alimentado por entropía física. Es el mejor sustituto disponible de una fuente ideal sin hardware cuántico, pero la diferencia medida es entre el MT19937 y una **fuente ideal modelada**, no frente a un dispositivo cuántico.
2. **Qiskit describe el proceso, pero no aporta la aleatoriedad.** La aleatoriedad la pone el sorteo. Esto también ocurría con Aer, solo que no se veía.
3. **La complejidad lineal requiere 10.000 claves.** Con 100 o 1.000 claves de 256 bits, la estructura del MT19937 no es observable.
4. **La IA por clave sigue sin distinguir las fuentes.** Es un resultado válido según el apartado "Alcance de la Interpretación". La diferencia aparece al analizar la secuencia completa, no en claves de 256 bits por separado.
5. **No es un ataque.** Medir la complejidad lineal no reconstruye ni predice claves. El estudio sigue sin intentar reconstruir el estado del generador, como establece el Alcance Tentativo.

## 5. Mensaje central sugerido

> Ni las pruebas estadísticas de primer orden ni cuatro modelos de IA distinguen las claves del MT19937 de las de una fuente cuántica ideal simulada: el Mersenne Twister cumple aquello para lo que fue diseñado. La complejidad lineal muestra, sin embargo, que sus bits siguen una regla lineal determinista limitada por su estado interno, y que dependen de una semilla de 32 bits, mientras que la fuente ideal no presenta estructura alguna. La calidad estadística no equivale a imprevisibilidad.
