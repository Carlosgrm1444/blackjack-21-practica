"""Blackjack 21: práctica de while para la Unidad 2.

Autor del juego de referencia: Carlos Gabriel Rodríguez Macías.
Las funciones del juego ya están listas; la actividad consiste en completar init.
Solo se usa la biblioteca estándar de Python. Las fichas son ficticias.
Consulta README.md para las reglas, el diagrama y los contratos de las funciones.
"""

import os
import random
import sys
import time


# ? Configuración de nuestra mesa. El dinero se guarda en centésimas de ficha:
# ? 200_000 significa 2000.00 fichas. Así evitamos errores de punto flotante.
SALDO_INICIAL = 200_000
APUESTA_MINIMA = 5_000
NUMERO_BARAJAS = 6
MAXIMO_MANOS = 4
CARTAS_PARA_REBARAJAR = 110
PAUSA_CRUPIER = 1.0
ANCHO_SEPARADOR = 64
RANGOS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
PALOS = ("Picas", "Corazones", "Diamantes", "Treboles")
# Usamos los símbolos sin el selector de emoji (️). Así cada palo ocupa
# exactamente una columna y las orillas de las cartas permanecen alineadas.
SIMBOLOS = {"Picas": "♠", "Corazones": "♥", "Diamantes": "♦", "Treboles": "♣"}

# ? Códigos ANSI: permiten colorear la consola sin instalar una librería.
# ? \033 significa "escape" y [91m, por ejemplo, activa el rojo brillante.
# ? Al terminar cada texto usamos \033[0m para regresar al color normal.
REINICIAR = "\033[0m"
NEGRITA = "\033[1m"
TENUE = "\033[2m"
ROJO = "\033[91m"
VERDE = "\033[92m"
AMARILLO = "\033[93m"
AZUL = "\033[94m"
MAGENTA = "\033[95m"
CIAN = "\033[96m"
BLANCO = "\033[97m"

# NO_COLOR es una convención para desactivar colores. isatty() evita guardar
# los códigos ANSI cuando la salida se manda a un archivo o a unas pruebas.
USAR_COLORES = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def pintar(texto, *estilos):
    """Rodea un texto con colores ANSI y restablece la consola al terminar.

    Ejemplo: pintar("Ganaste", NEGRITA, VERDE). Si la consola no acepta
    colores, devuelve el mismo texto sin códigos especiales.
    """
    texto = str(texto)
    if not USAR_COLORES or not estilos:
        return texto
    return "".join(estilos) + texto + REINICIAR


# ? Bloque 1: cartas reales y puntuación. No hay cartas elegidas con reemplazo.
def barajear():
    """Crea y mezcla seis barajas de 52 cartas, sin comodines: 312 cartas.

    Una carta es una tupla (rango, palo). Hay seis copias de cada combinación
    porque estamos usando seis barajas, no porque inventemos cartas al repartir.
    """
    mazo = []
    for _ in range(NUMERO_BARAJAS):
        for palo in PALOS:
            for rango in RANGOS:
                mazo.append((rango, palo))
    random.shuffle(mazo)
    return mazo


def dar_carta(juego, cartas):
    """Saca la última carta del zapato y la agrega a la lista recibida.

    pop() quita esa carta: no vuelve a salir durante este zapato. Las manos
    anteriores se descartan; solo se crea otro zapato entre rondas.
    """
    if not juego["mazo"]:
        raise RuntimeError("El zapato se agotó: revisa el rebarajado entre rondas.")
    cartas.append(juego["mazo"].pop())


def valor_carta(carta):
    """Devuelve el valor básico: as = 1, figuras = 10, números = su valor."""
    rango = carta[0]
    if rango == "A":
        return 1
    if rango in ("J", "Q", "K"):
        return 10
    return int(rango)


def calcular_total(cartas):
    """Devuelve el mejor total; usa un as como 11 cuando no excede 21.

    Primero todos los ases valen 1. Después podemos sumar 10 UNA vez:
    dos ases como 11 ya sumarían 22. Ejemplos: A+A+9 = 21, A+6+10 = 17.
    Se devuelve un número, nunca un texto como '7/17'.
    """
    total = 0
    tiene_as = False
    for carta in cartas:
        total += valor_carta(carta)
        if carta[0] == "A":
            tiene_as = True
    if tiene_as and total + 10 <= 21:
        total += 10
    return total


def es_mano_suave(cartas):
    """True si un as está contando como 11; esa mano puede bajar diez puntos."""
    total_basico = sum(valor_carta(carta) for carta in cartas)
    return calcular_total(cartas) > total_basico


def es_blackjack(cartas):
    """Detecta as + carta de valor 10 en exactamente dos cartas.

    El juego comprueba aparte si vienen de una separación: en ese caso, un
    total de 21 NO obtiene el pago especial de un blackjack natural.
    """
    return len(cartas) == 2 and calcular_total(cartas) == 21


# ? Bloque 2: entradas validadas. Sus while ya están hechos para la clase.
def preguntar_opcion(mensaje, opciones):
    """Repite la pregunta hasta recibir una clave válida del diccionario."""
    while True:
        respuesta = input(pintar(mensaje, NEGRITA, CIAN)).strip().lower()
        if respuesta in opciones:
            return respuesta
        print(pintar("⚠️  Opción inválida. Opciones disponibles: " + ", ".join(opciones), AMARILLO))


def preguntar_si_no(mensaje):
    """Acepta s, si, sí, n o no y devuelve True o False, no un texto."""
    opciones = {"s": True, "si": True, "sí": True, "n": False, "no": False}
    respuesta = preguntar_opcion(mensaje + " [s/n]: ", opciones)
    return opciones[respuesta]


def pedir_apuesta(juego):
    """Solicita fichas enteras, valida el saldo y devuelve centésimas.

    Esta función no descuenta fichas. preparar_ronda hace el descuento una vez
    que la entrada ya pasó todas las validaciones.
    """
    while True:
        mensaje = (
            f"💵 Apuesta (fichas enteras, mínimo {dinero(APUESTA_MINIMA)}, "
            f"saldo {dinero(juego['saldo'])}): "
        )
        texto = input(pintar(mensaje, NEGRITA, AMARILLO)).strip()
        try:
            apuesta = int(texto) * 100
        except ValueError:
            print(pintar("⚠️  Escribe un número entero, por ejemplo 50. No uses decimales.", AMARILLO))
            continue
        if apuesta < APUESTA_MINIMA:
            print(pintar("⚠️  La apuesta debe alcanzar el mínimo de la mesa.", AMARILLO))
        elif apuesta > juego["saldo"]:
            print(pintar("⚠️  No tienes suficientes fichas para esa apuesta.", AMARILLO))
        else:
            return apuesta


# ? Bloque 3: estado de la sesión y preparación de cada ronda.
def crear_juego():
    """Pide el nombre y devuelve un diccionario con todo el estado de sesión.

    init solo guarda este diccionario y lo pasa a las funciones. No necesita
    modificar sus claves ni usar variables globales.
    """
    nombre = input(pintar("👤 ¿Cómo te llamas? (Enter = Jugador): ", NEGRITA, CIAN)).strip() or "Jugador"
    return {
        "nombre": nombre,
        "saldo": SALDO_INICIAL,
        "mazo": [],
        "manos": [],
        "crupier": [],
        "indice_mano": 0,
        "ronda": 0,
        "seguro": 0,
        "crupier_visible": False,
        "liquidada": True,
        "saldo_inicio_ronda": SALDO_INICIAL,
        "estadisticas": {"ganadas": 0, "perdidas": 0, "empatadas": 0},
    }


def nueva_mano(cartas, apuesta, separada=False):
    """Agrupa las cartas, la apuesta y las banderas de UNA mano del jugador."""
    return {
        "cartas": cartas,
        "apuesta": apuesta,
        "separada": separada,
        "terminada": False,
        "rendida": False,
    }


def puede_apostar(juego):
    """True si el saldo disponible permite otra apuesta mínima."""
    return juego["saldo"] >= APUESTA_MINIMA


def preparar_ronda(juego):
    """Rebaraja si toca, cobra una apuesta válida y reparte las cuatro cartas.

    La reserva de 110 cartas cubre hasta cuatro manos y el crupier incluso
    con muchas cartas pequeñas. Nunca se rebaraja a mitad de una ronda.
    """
    if not juego["liquidada"]:
        raise RuntimeError("Liquida la ronda actual antes de preparar otra.")
    if not puede_apostar(juego):
        raise RuntimeError("No alcanza el saldo para una apuesta mínima.")
    if len(juego["mazo"]) <= CARTAS_PARA_REBARAJAR:
        juego["mazo"] = barajear()
        print(pintar("\n🔀 Se barajeó un zapato de seis barajas (312 cartas).", MAGENTA))

    apuesta = pedir_apuesta(juego)
    juego["saldo_inicio_ronda"] = juego["saldo"]
    juego["saldo"] -= apuesta
    juego["ronda"] += 1
    juego["manos"] = [nueva_mano([], apuesta)]
    juego["crupier"] = []
    juego["indice_mano"] = 0
    juego["seguro"] = 0
    juego["crupier_visible"] = False
    juego["liquidada"] = False

    # Reparto alternado: jugador, crupier, jugador, crupier.
    for _ in range(2):
        dar_carta(juego, juego["manos"][0]["cartas"])
        dar_carta(juego, juego["crupier"])
    print(pintar(f"\n{'═' * 64}\n🎲 RONDA {juego['ronda']} — apuesta {dinero(apuesta)} fichas", NEGRITA, CIAN))


def ofrecer_seguro(juego):
    """Con as visible, ofrece un seguro de la mitad de la apuesta inicial.

    Es una apuesta independiente. Solo se ofrece antes de consultar si hay
    blackjack, y requiere saldo adicional. Su resultado se paga al liquidar.
    """
    if juego["crupier"][0][0] != "A":
        return
    seguro = juego["manos"][0]["apuesta"] // 2
    if juego["saldo"] < seguro:
        print(pintar("⚠️  El crupier muestra un as; tu saldo no alcanza para el seguro.", AMARILLO))
        return
    print(pintar("🛡️  Seguro: ganas 2:1 si el crupier tiene blackjack; si no, lo pierdes.", AZUL))
    if preguntar_si_no(f"¿Comprar seguro por {dinero(seguro)} fichas?"):
        juego["saldo"] -= seguro
        juego["seguro"] = seguro


def hay_blackjack_inicial(juego):
    """True si el jugador o el crupier tiene blackjack en el reparto inicial.

    Con True se omiten AMBOS turnos y se pasa al pago. Ambos blackjack empatan.
    Esta consulta no imprime ni revela la carta oculta cuando devuelve False.
    """
    return es_blackjack(juego["manos"][0]["cartas"]) or es_blackjack(juego["crupier"])


# ? Bloque 4: acciones del jugador. init solo organiza su repetición.
def actualizar_turno_jugador(juego):
    """Avanza sobre las manos terminadas y prepara la siguiente mano separada.

    Al separar, la segunda mano conserva una sola carta hasta que le toca su
    turno. Así las cartas se entregan en orden, como en una mesa física.
    """
    while juego["indice_mano"] < len(juego["manos"]):
        mano = juego["manos"][juego["indice_mano"]]
        if mano["terminada"]:
            juego["indice_mano"] += 1
            continue
        if len(mano["cartas"]) == 1:
            dar_carta(juego, mano["cartas"])
        if calcular_total(mano["cartas"]) >= 21:
            mano["terminada"] = True
            continue
        break


def hay_turno_jugador(juego):
    """True si queda una mano por jugar. Avanza las manos ya terminadas.

    El while de init vuelve a llamar a esta función tras CADA acción. Pedir,
    plantarse, doblar, separar o rendirse cambian el estado que ella revisa.
    """
    actualizar_turno_jugador(juego)
    return juego["indice_mano"] < len(juego["manos"])


def acciones_disponibles(juego):
    """Devuelve solo las acciones legales de la mano actual y del saldo.

    Separar admite cartas del mismo valor (incluye, por ejemplo, J + K).
    Se permite doblar después de separar, excepto en ases separados.
    """
    mano = juego["manos"][juego["indice_mano"]]
    cartas = mano["cartas"]
    opciones = {"1": "🃏 Pedir carta", "2": "✋ Plantarse"}
    if len(cartas) == 2 and juego["saldo"] >= mano["apuesta"]:
        opciones["3"] = "💰 Doblar (una sola carta más)"
        if valor_carta(cartas[0]) == valor_carta(cartas[1]):
            if len(juego["manos"]) < MAXIMO_MANOS:
                opciones["4"] = "✂️  Separar el par en dos manos"
    if len(cartas) == 2 and not mano["separada"]:
        opciones["5"] = "🏳️  Rendirse (recuperar la mitad de la apuesta)"
    return opciones


def preguntar_accion(juego):
    """Imprime el menú válido y devuelve '1', '2', '3', '4' o '5'."""
    opciones = acciones_disponibles(juego)
    for clave, descripcion in opciones.items():
        print(pintar(f"  {clave}. {descripcion}", CIAN))
    return preguntar_opcion("Tu acción: ", opciones)


def separar_par(juego, mano):
    """Cobra otra apuesta e inserta la nueva mano justo después de la actual.

    Se pueden volver a separar pares hasta tener cuatro manos. Los ases se
    separan una sola vez, reciben una carta por mano y se plantan solos.
    """
    primera, segunda = mano["cartas"]
    juego["saldo"] -= mano["apuesta"]
    mano["cartas"] = [primera]
    mano["separada"] = True
    otra = nueva_mano([segunda], mano["apuesta"], separada=True)
    juego["manos"].insert(juego["indice_mano"] + 1, otra)
    if primera[0] == "A":
        dar_carta(juego, mano["cartas"])
        dar_carta(juego, otra["cartas"])
        mano["terminada"] = True
        otra["terminada"] = True
        print(pintar("✂️  Ases separados: una carta adicional por mano; ambas se plantan.", MAGENTA))
    else:
        print(pintar("✂️  Par separado: cada mano tiene su apuesta y su turno.", MAGENTA))


def aplicar_accion(juego, accion):
    """Ejecuta UNA acción y actualiza el turno, sin decidir el próximo menú.

    Incluso si se llama directamente, rechaza una acción no disponible antes
    de descontar fichas o repartir. init no necesita copiar estas reglas.
    """
    if accion not in acciones_disponibles(juego):
        raise ValueError("Esa acción no está disponible en esta mano.")
    mano = juego["manos"][juego["indice_mano"]]
    if accion == "1":
        dar_carta(juego, mano["cartas"])
        total = calcular_total(mano["cartas"])
        if total >= 21:
            mano["terminada"] = True
            mensaje = "🎯 ¡21! La mano se planta." if total == 21 else "💥 Te pasaste de 21."
            print(pintar(mensaje, VERDE if total == 21 else ROJO))
    elif accion == "2":
        mano["terminada"] = True
        print(pintar("✋ Te plantas con " + str(calcular_total(mano["cartas"])) + ".", AZUL))
    elif accion == "3":
        juego["saldo"] -= mano["apuesta"]
        mano["apuesta"] *= 2
        dar_carta(juego, mano["cartas"])
        mano["terminada"] = True
        print(pintar("💰 Apuesta doblada: se recibió una carta y terminó esta mano.", MAGENTA))
    elif accion == "4":
        separar_par(juego, mano)
    elif accion == "5":
        mano["rendida"] = True
        mano["terminada"] = True
        print(pintar("🏳️  Te rendiste; recuperarás la mitad al liquidar la ronda.", AMARILLO))
    actualizar_turno_jugador(juego)


# ? Bloque 5: el crupier sigue una regla FIJA, independiente de tu total.
def revelar_crupier(juego):
    """Destapa la carta oculta y muestra la mesa con los totales completos."""
    juego["crupier_visible"] = True
    print(pintar("\n🎩 El crupier revela su carta oculta.", NEGRITA, ROJO))
    mostrar_mesa(juego)


def debe_pedir_crupier(juego):
    """True si quedan manos en competencia y el crupier tiene menos de 17.

    Elegimos S17: se planta en TODOS los 17, incluso A + 6. Si todas las manos
    se pasaron o se rindieron, no pide cartas porque ya no hay qué comparar.
    """
    hay_mano_en_juego = any(
        not mano["rendida"] and calcular_total(mano["cartas"]) <= 21
        for mano in juego["manos"]
    )
    return hay_mano_en_juego and calcular_total(juego["crupier"]) < 17


def dar_carta_crupier(juego):
    """Reparte UNA carta al crupier. Su while decidirá si debe pedir otra."""
    dar_carta(juego, juego["crupier"])
    print(pintar("🃏 El crupier pide una carta.", ROJO))


def pausar_crupier():
    """Da tiempo para observar cada cambio durante el turno del crupier."""
    time.sleep(PAUSA_CRUPIER)


# ? Bloque 6: resultados y pagos. La apuesta ya salió del saldo al colocarla.
def resultado_mano(mano, crupier):
    """Devuelve (resultado, devolución) sin modificar el saldo.

    devolución incluye la apuesta que se recupera más la ganancia, si existe.
    Comprobar primero que el jugador se pasó evita empatar dos manos > 21.
    """
    apuesta = mano["apuesta"]
    total = calcular_total(mano["cartas"])
    total_crupier = calcular_total(crupier)
    natural = not mano["separada"] and es_blackjack(mano["cartas"])
    if mano["rendida"]:
        return "rendición", apuesta // 2
    if total > 21:
        return "derrota", 0
    if es_blackjack(crupier):
        if natural:
            return "empate", apuesta
        return "derrota", 0
    if natural:
        return "blackjack", apuesta + apuesta * 3 // 2
    if total_crupier > 21 or total > total_crupier:
        return "victoria", apuesta * 2
    if total == total_crupier:
        return "empate", apuesta
    return "derrota", 0


def liquidar_ronda(juego):
    """Paga seguro y manos UNA vez, muestra resultados y registra estadísticas."""
    if juego["liquidada"]:
        raise RuntimeError("Esta ronda ya fue liquidada; no se puede pagar dos veces.")
    mostrar_separador()
    print(pintar("\n🏁 RESULTADOS DE LA RONDA", NEGRITA, CIAN))
    if juego["seguro"]:
        if es_blackjack(juego["crupier"]):
            devolucion_seguro = juego["seguro"] * 3
            juego["saldo"] += devolucion_seguro
            print(pintar(f"✅ Seguro ganado: regresa {dinero(devolucion_seguro)} (apuesta + premio).", VERDE))
        else:
            print(pintar(f"❌ Seguro perdido: {dinero(juego['seguro'])} fichas.", ROJO))
    for numero, mano in enumerate(juego["manos"], start=1):
        resultado, devolucion = resultado_mano(mano, juego["crupier"])
        juego["saldo"] += devolucion
        if resultado in ("victoria", "blackjack"):
            juego["estadisticas"]["ganadas"] += 1
        elif resultado == "empate":
            juego["estadisticas"]["empatadas"] += 1
        else:
            juego["estadisticas"]["perdidas"] += 1
        balance = devolucion - mano["apuesta"]
        iconos = {"victoria": "✅", "blackjack": "🌟", "empate": "🤝", "derrota": "❌", "rendición": "🏳️"}
        color_resultado = VERDE if resultado in ("victoria", "blackjack") else AMARILLO if resultado == "empate" else ROJO
        mensaje = (
            f"{iconos[resultado]} Mano {numero}: {resultado}; apuesta {dinero(mano['apuesta'])}; "
            f"devuelve {dinero(devolucion)}; balance {dinero(balance)} fichas."
        )
        print(pintar(mensaje, color_resultado))
    juego["liquidada"] = True
    balance_ronda = juego["saldo"] - juego["saldo_inicio_ronda"]
    color_balance = VERDE if balance_ronda > 0 else ROJO if balance_ronda < 0 else AMARILLO
    print(pintar(f"Balance de la ronda (incluye seguro): {dinero(balance_ronda)} fichas.", color_balance))
    print(pintar(f"💰 Saldo disponible: {dinero(juego['saldo'])} fichas.", NEGRITA, AMARILLO))


def preguntar_otra_ronda():
    """True si el jugador quiere continuar; False si desea terminar."""
    return preguntar_si_no("\n¿Jugar otra ronda?")


# ? Bloque 7: presentación con emojis y colores ANSI para la terminal.
def dinero(centesimas):
    """Formatea centésimas sin convertirlas a float, incluidos balances negativos."""
    signo = "-" if centesimas < 0 else ""
    cantidad = abs(centesimas)
    return f"{signo}{cantidad // 100}.{cantidad % 100:02d}"


def mostrar_separador():
    """Separa visualmente una interacción de la siguiente."""
    print(pintar("\n" + "-" * ANCHO_SEPARADOR, TENUE, BLANCO))


def dibujar_cartas(cartas, ocultar_segunda=False):
    """Muestra cartas con símbolos de palos; nunca imprime una carta tapada."""
    caras = []
    for indice, carta in enumerate(cartas):
        if ocultar_segunda and indice > 0:
            reverso = ["╔═══════╗", "║░░░░░░░║", "║░░░╳░░░║", "║░░░░░░░║", "╚═══════╝"]
            caras.append([pintar(linea, MAGENTA, TENUE) for linea in reverso])
        else:
            rango, palo = carta
            cara = [
                "┌───────┐",
                f"│{rango:<7}│",
                f"│   {SIMBOLOS[palo]}   │",
                f"│{rango:>7}│",
                "└───────┘",
            ]
            color_palo = ROJO if palo in ("Corazones", "Diamantes") else CIAN
            caras.append([pintar(linea, NEGRITA, color_palo) for linea in cara])
    for inicio in range(0, len(caras), 6):
        grupo = caras[inicio:inicio + 6]
        for fila in range(5):
            print(" ".join(cara[fila] for cara in grupo))


def texto_total(cartas):
    """Muestra el mejor total y aclara si es suave o si ya se pasó."""
    total = calcular_total(cartas)
    if total > 21:
        return f"{total} (se pasó)"
    if es_mano_suave(cartas):
        return f"{total} (suave: un as vale 11)"
    return str(total)


def mostrar_mesa(juego):
    """Imprime saldo, cartas y apuestas; oculta también el TOTAL del crupier."""
    mostrar_separador()
    print(pintar("\n💰 SALDO", NEGRITA, AMARILLO))
    print(pintar(f"   Disponible: {dinero(juego['saldo'])} fichas", AMARILLO))

    print(pintar("\n🎩 CRUPIER", NEGRITA, ROJO))
    if juego["crupier_visible"]:
        print(pintar("   Total: " + texto_total(juego["crupier"]), ROJO))
    else:
        visible = juego["crupier"][:1]
        print(pintar("   Carta visible: " + texto_total(visible), ROJO))
        print(pintar("   Total: oculto", ROJO))
    dibujar_cartas(juego["crupier"], ocultar_segunda=not juego["crupier_visible"])

    for indice, mano in enumerate(juego["manos"]):
        es_turno = indice == juego["indice_mano"] and not mano["terminada"]
        color_mano = VERDE if es_turno else AZUL
        print(pintar(f"\n👤 JUGADOR: {juego['nombre']}", NEGRITA, color_mano))
        print(pintar(f"   Mano: {indice + 1}", color_mano))
        print(pintar(f"   Total: {texto_total(mano['cartas'])}", color_mano))
        print(pintar(f"   Apuesta: {dinero(mano['apuesta'])} fichas", color_mano))
        if es_turno:
            print(pintar("   Estado: 👈 TU TURNO", NEGRITA, VERDE))
        dibujar_cartas(mano["cartas"])


def mostrar_bienvenida(juego):
    """Resume las reglas que necesita conocer quien va a jugar."""
    print(pintar(f"\n{'═' * 64}", NEGRITA, MAGENTA))
    print(pintar(f"🃏 ¡Bienvenido, {juego['nombre']}, a BLACKJACK 21! 🎰", NEGRITA, MAGENTA))
    print(pintar("═" * 64, NEGRITA, MAGENTA))
    print(pintar(f"💰 Empiezas con {dinero(juego['saldo'])} fichas ficticias; mínimo 50 por ronda.", AMARILLO))
    print("🎯 Gana al crupier sin pasar de 21. Figuras = 10; as = 1 u 11.")
    print("🏆 Victoria paga 1:1; blackjack natural paga 3:2; empate devuelve apuesta.")
    print("🎩 Crupier: pide hasta 16, se planta en 17 (incluye 17 suave).")
    print("🃏 Puedes pedir, plantarte, doblar, separar hasta cuatro manos o rendirte.")
    print("💵 Doblar/separar necesitan otra apuesta; ases separados reciben una carta.")
    print("🛡️  Seguro opcional con as visible; rendición solo en la mano original de dos cartas.")
    print("Palos: ♠ picas · ♥ corazones · ♦ diamantes · ♣ tréboles.")


def mostrar_despedida(juego):
    """Indica por qué termina la sesión y resume las manos, no las rondas."""
    if not puede_apostar(juego):
        print(pintar("\n⚠️  Tu saldo ya no alcanza para la apuesta mínima de 50 fichas.", AMARILLO))
    estadisticas = juego["estadisticas"]
    print(pintar(f"\n🎰 Gracias por jugar, {juego['nombre']}. Rondas: {juego['ronda']}.", NEGRITA, MAGENTA))
    print(
        f"Manos ganadas: {estadisticas['ganadas']}; "
        f"perdidas (incluye rendición): {estadisticas['perdidas']}; "
        f"empatadas: {estadisticas['empatadas']}."
    )
    print(pintar(f"💰 Saldo final: {dinero(juego['saldo'])} fichas.", NEGRITA, AMARILLO))
    balance = juego["saldo"] - SALDO_INICIAL
    color_balance = VERDE if balance > 0 else ROJO if balance < 0 else AMARILLO
    print(pintar(f"📊 Balance de sesión: {dinero(balance)} fichas.", NEGRITA, color_balance))


# ? Bloque 8: ÚNICA función que cambia entre la práctica y la solución.
def init():
    """TODO: completa aquí la sesión siguiendo README.md y el diagrama.

    Solo debes cambiar esta función. Las funciones del juego están listas.
    Necesitas tres while: rondas, acciones del jugador y cartas del crupier.
    """
    # ? 1. Crea el juego y muestra la bienvenida.
    # ? 2. Crea una bandera booleana para indicar si quiere seguir jugando.
    # ? 3. Mientras quiera seguir Y pueda apostar, organiza una ronda:
    # ?    a) Prepara la ronda, muestra la mesa y ofrece el seguro.
    # ?    b) Consulta si hay blackjack inicial.
    # ?    c) Si NO lo hay, repite las acciones del jugador con otro while.
    # ?       En cada vuelta: pregunta y aplica una acción.
    # ?       Si todavía hay turno, muestra la mesa actualizada.
    # ?       Después revela las cartas del crupier y llama pausar_crupier().
    # ?       Con un tercer while, dale una carta cuando deba pedir, muestra
    # ?       la mesa y llama pausar_crupier() para ver cada carta por separado.
    # ?    d) Si SÍ hay blackjack inicial, revela el crupier y haz la pausa.
    # ?    e) Liquida la ronda UNA vez, después de los turnos o del blackjack.
    # ?    f) Si alcanza para otra apuesta, pregunta si desea continuar.
    # ?       Guarda la respuesta en la bandera; preguntar solo no la cambia.
    # ? 4. Después del while principal, muestra la despedida.
    # ? Sustituye este mensaje por tu implementación:
    print("Práctica pendiente: completa init() siguiendo README.md.")


if __name__ == "__main__":
    # Se puede importar para comprobar funciones sin iniciar una partida.
    try:
        init()
    except (KeyboardInterrupt, EOFError):
        print("\nSesión interrumpida. Las fichas son ficticias y no se guardan.")
