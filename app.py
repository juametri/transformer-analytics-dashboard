import math
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# ==========================================
# 1. PARTE MATEMÁTICA
# ==========================================


def calcular_circuito_abierto(v_ca, i_ca, p_ca):
    if v_ca <= 0 or i_ca <= 0 or p_ca <= 0:
        return None, None
    cos_theta = p_ca / (v_ca * i_ca)
    if cos_theta < 0 or cos_theta > 1.001:
        return None, None
    cos_theta = min(1.0, max(0.0, cos_theta))
    theta = math.acos(cos_theta)
    sin_theta = math.sin(theta)
    y_m = i_ca / v_ca
    g_m = y_m * cos_theta
    b_m = y_m * sin_theta
    if g_m == 0 or b_m == 0:
        return None, None
    return 1 / g_m, 1 / b_m


def calcular_cortocircuito(v_cc, i_cc, p_cc):
    if v_cc <= 0 or i_cc <= 0 or p_cc <= 0:
        return None, None
    cos_theta = p_cc / (v_cc * i_cc)
    if cos_theta > 1.001:
        return None, None
    z_eq = v_cc / i_cc
    r_eq = p_cc / (i_cc**2)
    if z_eq < r_eq:
        return None, None
    x_eq = math.sqrt(max(0, z_eq**2 - r_eq**2))
    return r_eq, x_eq


def simular_operacion_transformador(
    s_nom, v2_nom, r_eq, x_eq, p_vacio, fp, tipo_fp="atraso"
):
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


# ==========================================
# 2. INTERFAZ GRÁFICA WEB (STREAMLIT)
# ==========================================

# Configuración de la página web para que use pantalla ancha
st.set_page_config(
    page_title="Dashboard de Transformadores", layout="wide"

)

st.title("Calculadora de Parámetros de Transformadores")
st.markdown(
    "Modifica los valores en la barra lateral izquierda para recalcular todos los parametros del transformador "
)

# --- BARRA LATERAL IZQUIERDA (INPUTS) ---
with st.sidebar:
    st.header("Parámetros")

    st.subheader("Datos Nominales")
    s_nom = st.number_input("Potencia Nominal (VA):", value=15000)
    v2_nom = st.number_input("Voltaje Secundario (V):", value=240)
    fp_sim = st.slider(
        "F.P. Simulación:", min_value=0.1, max_value=1.0, value=0.8, step=0.005
    )

    st.subheader("Prueba de Vacío (CA)")
    v_ca = st.number_input("Voltaje V_ca (V):", value=240)
    i_ca = st.number_input("Corriente I_ca (A):", value=1.5)
    p_ca = st.number_input("Potencia P_ca (W):", value=180)

    st.subheader("Prueba Cortocircuito (CC)")
    v_cc = st.number_input("Voltaje V_cc (V):", value=48)
    i_cc = st.number_input("Corriente I_cc (A):", value=62.5)
    p_cc = st.number_input("Potencia P_cc (W):", value=600)

# --- PROCESAMIENTO DE DATOS ---
r_m, x_m = calcular_circuito_abierto(v_ca, i_ca, p_ca)
r_eq, x_eq = calcular_cortocircuito(v_cc, i_cc, p_cc)

if r_m and x_m and r_eq and x_eq:
    indices, eficiencias, regulaciones, x_max_ef = (
        simular_operacion_transformador(
            s_nom, v2_nom, r_eq, x_eq, p_ca, fp_sim, tipo_fp="atraso"
        )
    )

    #LIENZO DE MATPLOTLIB 5 paneles
    fig = plt.figure(figsize=(12, 8), tight_layout=True)
    gs = fig.add_gridspec(2, 3)

    ax_circuito = fig.add_subplot(gs[0, 0:2])
    ax_tabla = fig.add_subplot(gs[0, 2])
    ax_eficiencia = fig.add_subplot(gs[1, 0])
    ax_regulacion = fig.add_subplot(gs[1, 1])
    ax_fasores = fig.add_subplot(gs[1, 2])

    # --- PANEL CIRCUITO ---
    ax_circuito.axis("off")
    ax_circuito.set_xlim(0, 10)
    ax_circuito.set_ylim(0, 6)
    ax_circuito.plot([0, 1], [5, 5], color="black", linewidth=2)
    ax_circuito.plot([2, 5], [5, 5], color="black", linewidth=2)
    ax_circuito.plot([6, 8], [5, 5], color="black", linewidth=2)
    ax_circuito.plot([0, 8], [1, 1], color="black", linewidth=2)

    # Cables verticales hacia la rama paralelo (Techo)
    ax_circuito.plot([2.5, 2.5], [5, 4], color="black", linewidth=2)
    ax_circuito.plot([3.5, 3.5], [5, 4], color="black", linewidth=2)

    # Cables verticales hacia la rama paralelo (Piso)
    ax_circuito.plot([2.5, 2.5], [2.5, 1], color="black", linewidth=2)
    ax_circuito.plot([3.5, 3.5], [2.5, 1], color="black", linewidth=2)

# Dibujo de los bloques de los componentes (Alineación corregida)
    rect_req = plt.Rectangle((1, 4.7), 1.0, 0.6, facecolor="#ff7f0e", edgecolor="black", alpha=0.8)
    rect_xeq = plt.Rectangle((5, 4.7), 1.0, 0.6, facecolor="#9467bd", edgecolor="black", alpha=0.8)
    rect_rm = plt.Rectangle((2.2, 2.5), 0.6, 1.5, facecolor="#2ca02c", edgecolor="black", alpha=0.8)
    rect_xm = plt.Rectangle((3.2, 2.5), 0.6, 1.5, facecolor="#1f77b4", edgecolor="black", alpha=0.8)
    ax_circuito.add_patch(rect_req)
    ax_circuito.add_patch(rect_xeq)
    ax_circuito.add_patch(rect_rm)
    ax_circuito.add_patch(rect_xm)

    # 3. COLOCACIÓN DE TEXTOS EN FILA VERTICAL PERFECTA (Sin estorbar a las líneas)

    # Componentes Serie (Arriba)
    ax_circuito.text(1.5, 5.5, "Req", fontsize=10, weight="bold", ha="center")
    ax_circuito.text(1.5, 4.2, f"{r_eq:.2f} Ω", fontsize=9, ha="center", backgroundcolor="white")

    ax_circuito.text(5.5, 5.5, "Xeq", fontsize=10, weight="bold", ha="center")
    ax_circuito.text(5.5, 4.2, f"{x_eq:.2f} Ω", fontsize=9, ha="center", backgroundcolor="white")

    # --- Componentes Paralelo (En Torres Perfectas) ---

    # Nombres "Rm" y "Xm" flotando JUSTO ARRIBA de las cajas (Las cajas empiezan en Y=3.0 y terminan en Y=4.2)
    # Al ponerlos en Y=4.4 con ha="center", se alinean perfecto sobre sus cables superiores
    ax_circuito.text(2.5, 4.4, "Rm", fontsize=10, weight="bold", ha="center", backgroundcolor="white")
    ax_circuito.text(3.5, 4.4, "Xm", fontsize=10, weight="bold", ha="center", backgroundcolor="white")

    # Valores numéricos en Ohmios flotando ABAJO en el espacio vacío (Y=2.0)
    # Como el cable baja hasta Y=1.0, la altura Y=2.0 queda exactamente a la mitad del cable.
    # El truco 'backgroundcolor="white"' va a borrar la línea negra que pase por detrás del número.
    ax_circuito.text(2.5, 2.0, f"{r_m:.1f} Ω", fontsize=9, ha="center", backgroundcolor="white")
    ax_circuito.text(3.5, 2.0, f"{x_m:.1f} Ω", fontsize=9, ha="center", backgroundcolor="white")


    ax_circuito.set_title(
        "Circuito Equivalente Aproximado", fontsize=10, weight="bold"
    )

    # --- PANEL TABLA ---
    ax_tabla.axis("off")
    ax_tabla.text(
        0.05,
        0.90,
        "REPORTE DE PARÁMETROS",
        fontsize=11,
        weight="bold",
        color="#1f538d",
    )
    ax_tabla.text(
        0.05, 0.75, " Rama de Vacío (Núcleo):", fontsize=10, weight="bold"
    )
    ax_tabla.text(0.10, 0.67, f"• Rm (Pérdidas) = {r_m:.2f} \Omega", fontsize=10)
    ax_tabla.text(
        0.10, 0.59, f"• Xm (Magnetiz.) = {x_m:.2f} \Omega", fontsize=10
    )
    ax_tabla.text(
        0.05, 0.45, " Rama Serie (Cobre):", fontsize=10, weight="bold"
    )
    ax_tabla.text(0.10, 0.37, f"• Req (Resist.) = {r_eq:.2f} \Omega", fontsize=10)
    ax_tabla.text(0.10, 0.29, f"• Xeq (React.) = {x_eq:.2f} \Omega", fontsize=10)
    ax_tabla.text(
        0.05, 0.15, " Rendimiento Óptimo:", fontsize=10, weight="bold"
    )
    ax_tabla.text(
        0.10,
        0.07,
        f"• Carga \eta Máx = {x_max_ef*100:.1f}%",
        fontsize=10,
        color="red",
    )

    # --- PANEL EFICIENCIA ---
    porcentaje_carga = [i * 100 for i in indices]
    _, ef_unitario, _, _ = simular_operacion_transformador(
        s_nom, v2_nom, r_eq, x_eq, p_ca, 1.0, tipo_fp="atraso"
    )
    _, ef_bajo, _, _ = simular_operacion_transformador(
        s_nom, v2_nom, r_eq, x_eq, p_ca, 0.6, tipo_fp="atraso"
    )

    ax_eficiencia.plot(
        porcentaje_carga,
        ef_unitario,
        label="FP = 1.0",
        linestyle="--",
        color="#2ca02c",
    )
    ax_eficiencia.plot(
        porcentaje_carga,
        eficiencias,
        label=f"FP = {fp_sim}",
        linewidth=2,
        color="#1f77b4",
    )
    ax_eficiencia.plot(
        porcentaje_carga,
        ef_bajo,
        label="FP = 0.6",
        linestyle=":",
        color="#ff7f0e",
    )

    p_out_max = x_max_ef * s_nom * fp_sim
    i_nom_sec = s_nom / v2_nom
    p_cu_max = (x_max_ef**2) * (i_nom_sec**2) * r_eq
    ef_maxima_ponto = (p_out_max / (p_out_max + p_ca + p_cu_max)) * 100
    ax_eficiencia.plot(
        x_max_ef * 100,
        ef_maxima_ponto,
        "ro",
        markersize=8,
        label=f"\eta Máx ({x_max_ef*100:.1f}%)",
    )

    ax_eficiencia.set_title(
        "Curva de Eficiencia (\eta)", fontsize=10, weight="bold"
    )
    ax_eficiencia.set_xlabel("% de Carga Nominal", fontsize=9)
    ax_eficiencia.set_ylabel("Eficiencia (%)", fontsize=9)
    ax_eficiencia.grid(True, linestyle="--", alpha=0.5)
    ax_eficiencia.legend(fontsize=8, loc="lower right")

    # --- PANEL REGULACIÓN ---
    _, _, vr_unitario, _ = simular_operacion_transformador(
        s_nom, v2_nom, r_eq, x_eq, p_ca, 1.0, tipo_fp="atraso"
    )
    _, _, vr_adelanto, _ = simular_operacion_transformador(
        s_nom, v2_nom, r_eq, x_eq, p_ca, 0.8, tipo_fp="adelanto"
    )

    ax_regulacion.plot(
        porcentaje_carga,
        regulaciones,
        label=f"FP = {fp_sim} (Atraso)",
        linewidth=2,
        color="#1f77b4",
    )
    ax_regulacion.plot(
        porcentaje_carga,
        vr_unitario,
        label="FP = 1.0",
        linestyle="--",
        color="#2ca02c",
    )
    ax_regulacion.plot(
        porcentaje_carga,
        vr_adelanto,
        label="FP = 0.8 (Adelanto)",
        linestyle="-.",
        color="#d62728",
    )
    ax_regulacion.set_title(
        "Regulación de Voltaje (VR%)", fontsize=10, weight="bold"
    )
    ax_regulacion.set_xlabel("% de Carga Nominal", fontsize=9)
    ax_regulacion.set_ylabel("Regulación (%)", fontsize=9)
    ax_regulacion.grid(True, linestyle="--", alpha=0.5)
    ax_regulacion.legend(fontsize=8, loc="upper left")
    ax_regulacion.axhline(0, color="black", linewidth=0.8, linestyle="-")

    # --- PANEL FASORES ---
    v2_vec = complex(v2_nom, 0)
    angulo_rad = -np.arccos(fp_sim)
    i_vec = (i_nom_sec) * (np.cos(angulo_rad) + 1j * np.sin(angulo_rad))
    v_req_vec = i_vec * r_eq
    v_xeq_vec = i_vec * (1j * x_eq)
    v1_vec = v2_vec + v_req_vec + v_xeq_vec

    ax_fasores.quiver(
        0,
        0,
        v2_vec.real,
        v2_vec.imag,
        angles="xy",
        scale_units="xy",
        scale=1,
        color="#1f77b4",
        label="V2",
    )
    escala_i = v2_nom / (i_nom_sec * 2)
    ax_fasores.quiver(
        0,
        0,
        i_vec.real * escala_i,
        i_vec.imag * escala_i,
        angles="xy",
        scale_units="xy",
        scale=1,
        color="#2ca02c",
        label="I (Esc)",
    )
    ax_fasores.quiver(
        v2_vec.real,
        v2_vec.imag,
        v_req_vec.real,
        v_req_vec.imag,
        angles="xy",
        scale_units="xy",
        scale=1,
        color="#ff7f0e",
        label="I*Req",
    )
    ax_fasores.quiver(
        v2_vec.real + v_req_vec.real,
        v2_vec.imag + v_req_vec.imag,
        v_xeq_vec.real,
        v_xeq_vec.imag,
        angles="xy",
        scale_units="xy",
        scale=1,
        color="#9467bd",
        label="I*jXeq",
    )
    ax_fasores.quiver(
        0,
        0,
        v1_vec.real,
        v1_vec.imag,
        angles="xy",
        scale_units="xy",
        scale=1,
        color="#d62728",
        label="V1",
    )

    max_x = max(v2_vec.real, v1_vec.real) * 1.1
    min_x = min(0, i_vec.real * escala_i) * 1.3
    max_y = max(v1_vec.imag, v_xeq_vec.imag, 0) * 1.5
    min_y = min(0, i_vec.imag * escala_i) * 1.3
    ax_fasores.set_xlim(min_x, max_x)
    ax_fasores.set_ylim(min_y, max_y)
    ax_fasores.set_title(
        "Diagrama Fasorial (Nominal)", fontsize=10, weight="bold"
    )
    ax_fasores.grid(True, linestyle="--", alpha=0.3)
    ax_fasores.legend(fontsize=7, loc="upper left")

    # MANDA LA FIGURA COMPLETA A LA WEB
    st.pyplot(fig)

else:
    st.error(
        "No se pudieron calcular los parámetros. Revisa los datos de entrada en la barra lateral."
    )