import math
import numpy as np


def calcular_circuito_abierto(v_ca, i_ca, p_ca):
    """
    Calcula los parámetros de la rama de magnetización (Rm y Xm).
    """
    if v_ca <= 0 or i_ca <= 0 or p_ca <= 0:
        print(
            "[Error Prueba Vacío]: Los valores de voltaje, corriente y potencia deben ser mayores a cero."
        )
        return None, None

    cos_theta = p_ca / (v_ca * i_ca)

    # Permitimos hasta 1.001 por errores de redondeo flotante de la PC
    if cos_theta < 0 or cos_theta > 1.001:
        print(
            f"[Error Prueba Vacío]: Datos imposibles. El factor de potencia ({cos_theta:.3f}) no está entre 0 y 1."
        )
        return None, None

    cos_theta = min(1.0, max(0.0, cos_theta))

    theta = math.acos(cos_theta)
    sin_theta = math.sin(theta)
    y_m = i_ca / v_ca
    g_m = y_m * cos_theta
    b_m = y_m * sin_theta

    if g_m == 0 or b_m == 0:
        return None, None

    r_m = 1 / g_m
    x_m = 1 / b_m
    return r_m, x_m


def calcular_cortocircuito(v_cc, i_cc, p_cc):
    """
    Calcula los parámetros de los devanados en serie (Req y Xeq) con protecciones.
    """
    if v_cc <= 0 or i_cc <= 0 or p_cc <= 0:
        print(
            "[Error Cortocircuito]: Los valores de voltaje, corriente y potencia deben ser mayores a cero."
        )
        return None, None

    cos_theta = p_cc / (v_cc * i_cc)
    if cos_theta > 1.001:
        print(
            f"[Error Cortocircuito]: Potencia ingresada ({p_cc}W) supera la potencia aparente nominal ({v_cc * i_cc:.2f}VA)."
        )
        return None, None

    z_eq = v_cc / i_cc
    r_eq = p_cc / (i_cc**2)

    if z_eq < r_eq:
        print(
            "[Error Cortocircuito]: Inconsistencia. La resistencia es mayor que la impedancia total."
        )
        return None, None

    x_eq = math.sqrt(max(0, z_eq**2 - r_eq**2))
    return r_eq, x_eq


def simular_operacion_transformador(
    s_nom, v2_nom, r_eq, x_eq, p_vacio, fp, tipo_fp="atraso"
):
    """
    Calcula las curvas de eficiencia, regulación y fasores para un FP dado.
    """
    indices_carga = np.linspace(0.01, 1.2, 100)
    i_nom_sec = s_nom / v2_nom
    angulo_rad = np.arccos(fp)

    if tipo_fp == "atraso":
        angulo_rad = -angulo_rad

    eficiencias = []
    regulaciones = []

    for x in indices_carga:
        p_out = x * s_nom * fp
        p_cu = (x**2) * (i_nom_sec**2) * r_eq
        en_ef = (p_out / (p_out + p_vacio + p_cu)) * 100
        eficiencias.append(en_ef)

        i_compleja = (x * i_nom_sec) * (
            np.cos(angulo_rad) + 1j * np.sin(angulo_rad)
        )
        v1_complejo = v2_nom + i_compleja * complex(r_eq, x_eq)
        vr = ((abs(v1_complejo) - v2_nom) / v2_nom) * 100
        regulaciones.append(vr)

    p_cu_nominal = (i_nom_sec**2) * r_eq
    x_max_ef = np.sqrt(p_vacio / p_cu_nominal)

    return list(indices_carga), eficiencias, regulaciones, x_max_ef


# --- FLUJO PRINCIPAL DEL PROGRAMA ---
if __name__ == "__main__":
    print("=" * 50)
    print(" CALCULADORA DE PARÁMETROS DE TRANSFORMADORES")
    print("=" * 50)

    # NUEVO: Datos nominales para poder correr la simulación
    print("\n>>> DATOS NOMINALES DE PLACA:")
    s_nom = float(input("Potencia aparente nominal (S_nom) [VA]: "))
    v2_nom = float(input("Voltaje nominal secundario (V2_nom) [V]: "))
    fp_sim = float(
        input("Factor de potencia para la simulación (ej. 0.8): ")
    )

    # Sección 1: Datos de Vacío
    print("\n>>> DATOS DE LA PRUEBA DE VACÍO (Lado de Baja Tensión):")
    v_ca = float(input("Voltaje de circuito abierto (V_ca) [V]: "))
    i_ca = float(input("Corriente de circuito abierto (I_ca) [A]: "))
    p_ca = float(input("Potencia de circuito abierto (P_ca) [W]: "))

    # Sección 2: Datos de Cortocircuito
    print("\n>>> DATOS DE LA PRUEBA DE CORTOCIRCUITO (Lado de Alta Tensión):")
    v_cc = float(input("Voltaje de cortocircuito (V_cc) [V]: "))
    i_cc = float(input("Corriente de cortocircuito (I_cc) [A]: "))
    p_cc = float(input("Potencia de cortocircuito (P_cc) [W]: "))

    # Ejecución de Cálculos de Parámetros
    r_m, x_m = calcular_circuito_abierto(v_ca, i_ca, p_ca)
    r_eq, x_eq = calcular_cortocircuito(v_cc, i_cc, p_cc)

    print("\n" + "=" * 50)
    print(" RESULTADOS DEL ANÁLISIS")
    print("=" * 50)

    # Impresión de la rama de vacío
    if r_m is not None and x_m is not None:
        print(f"Rm (Pérdidas núcleo): {r_m:.2f} Ω")
        print(f"Xm (Magnetización):   {x_m:.2f} Ω")
    else:
        print(
            "No se pudieron calcular Rm y Xm debido a errores en datos de vacío."
        )

    print("-" * 50)

    # Impresión de la rama serie e inicio de simulación de carga
    if r_eq is not None and x_eq is not None:
        print(f"Req (Resistencia equivalente): {r_eq:.2f} Ω")
        print(f"Xeq (Reactancia equivalente):  {x_eq:.2f} Ω")
        print("-" * 50)

        # Usamos p_ca como las pérdidas de vacío fijas para la eficiencia
        indices, eficiencias, regulaciones, x_max_ef = (
            simular_operacion_transformador(
                s_nom, v2_nom, r_eq, x_eq, p_ca, fp_sim, tipo_fp="atraso"
            )
        )

        # Mostramos los resultados de la simulación
        print(f"Simulación ejecutada a un FP de: {fp_sim}")
        print(
            f"La eficiencia MÁXIMA ocurrirá al {x_max_ef * 100:.1f}% de la carga nominal."
        )
        print(
            f"Eficiencia al 100% de carga: {eficiencias[82]:.2f}%"
        )  # Muestra un punto estimado de la lista
        print(
            f"Regulación de voltaje al 100% de carga: {regulaciones[82]:.2f}%"
        )
    else:
        print(
            "No se pudo simular la operación porque fallaron los cálculos de cortocircuito."
        )

    print("=" * 50)