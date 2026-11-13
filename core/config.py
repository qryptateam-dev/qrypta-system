"""Parámetros únicos del simulador (fuente de verdad para todos los módulos)."""
LONGITUDES_CLAVE = (64, 128, 256)    # bits por clave que puede elegir el usuario (RN-001)
LONGITUD_ESTUDIO = 256               # longitud fija de la muestra del estudio (Anteproyecto, 7.4)
CANTIDADES_CLAVES = (100, 1_000, 10_000)   # volumen de claves por generador (condición experimental)
N_QUBITS = 16                        # M2: qubits medidos por shot
LAGS_AUTOCORRELACION = 16            # M3: desplazamientos del análisis global
LAGS_POR_CLAVE = 8                   # M3/M4: desplazamientos usados como indicadores de cada clave
ALFA = 0.01                          # umbral de p-valor (pruebas NIST y clasificación frente al azar)
PROPORCION_PRUEBA = 0.30             # M4: 70 % entrenamiento / 30 % prueba
SEMILLA_MODELOS = 42                 # M4: reproducibilidad de la partición y de los modelos
ETIQUETA_PRNG, ETIQUETA_QRNG = 1, 0  # clase positiva = PRNG (sensibilidad); negativa = QRNG (especificidad)
DECIMACION_COMPLEJIDAD = 32          # M3: complejidad lineal sobre 1 de cada 32 bits (un bit por palabra de 32 bits)
GRADO_MT19937 = 19937                # complejidad lineal máxima del Mersenne Twister (grado de su recurrencia)
