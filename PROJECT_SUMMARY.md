# Project Summary - Burj Nawas Mass Concrete Thermal Simulation

This document provides a comprehensive technical overview of the Burj Nawas Concrete Thermal Simulation application. It details the engineering standards, mathematical calculations, boundary conditions, and code structure utilized by the app.

---

## 1. Application Overview
The application is a web-based engineering tool built with **Streamlit** (Python). It is designed to validate mix designs and curing conditions for mass concrete components—specifically the thick raft foundations of the **Burj Nawas** project—to prevent early-age cracking and structural deterioration.

---

## 2. Engineering Reference Standards

The thermal model and calculations are strictly based on internationally recognized codes:

1. **ACI 207.1R ("Guide to Mass Concrete")**: Sourced for adiabatic temperature rise formulas, SCM hydration contribution factors, and slab thickness thermal inertia correction.
2. **ACI 207.2R ("Report on Thermal and Volume Change Effects on Cracking of Mass Concrete")**: Defines the maximum allowable core-to-surface thermal differential limit.
3. **ASTM C494 ("Standard Specification for Chemical Admixtures for Concrete")**: Governs the modeling of Type B (retarding) and Type D (water-reducing and retarding) admixtures on cement setting delays.
4. **ASTM C177 / C351**: Governs standard testing parameters for concrete specific heat capacity ($c$) and thermal conductivity ($K$).

---

## 3. Input Parameters

### A. Core Controls
* **Placement Temperature ($T_{\text{place}}$)**: Initial temperature of concrete immediately after batching and pouring ($10.0^\circ\text{C}$ to $45.0^\circ\text{C}$).
* **Mean Ambient Temperature ($T_{\text{amb}}$)**: Average expected ambient curing temperature ($10.0^\circ\text{C}$ to $50.0^\circ\text{C}$).
* **Raft Thickness ($H$)**: Structural thickness of the foundation slab in centimeters ($50\text{ cm}$ to $500\text{ cm}$).

### B. Mix Chemistry (Expander)
* **Cement, GGBFS (Slag), and Silica Fume Contents**: Mix proportions per cubic meter of concrete ($\text{kg/m}^3$).
* **Cement Type (ACI 207)**: Pre-calibrated heats of hydration ($H_u$, $\text{kJ/kg}$):
  * Type I (General Purpose): $350 \text{ kJ/kg}$
  * Type II (Moderate Heat): $300 \text{ kJ/kg}$
  * Type III (High Early Strength): $390 \text{ kJ/kg}$
  * Type IV (Low Heat): $250 \text{ kJ/kg}$
  * Type V (Sulfate Resistant): $310 \text{ kJ/kg}$
  * Custom Heat Profile: User-defined $H_u$ value ($150 - 500\text{ kJ/kg}$).

### C. Concrete Thermal Properties (Expander)
* **Specific Heat ($c$)**: Specific heat capacity of concrete ($800 - 1200\text{ J/kg}\cdot\text{K}$).
* **Thermal Conductivity ($K$)**: Rate of thermal transmission ($1.5 - 3.5\text{ W/m}\cdot\text{K}$).

### D. Curing & Insulation (Expander)
* **Insulation Method**: Governs boundary thermal resistance:
  * Bare Concrete ($\text{insulation factor} = 1.0$)
  * Plastic Sheeting ($\text{insulation factor} = 0.75$)
  * Single Insulation Blanket R-1.0 ($\text{insulation factor} = 0.40$)
  * Double Insulation Blanket R-2.0 ($\text{insulation factor} = 0.15$)

### E. Environment & Admixtures (Expander)
* **Diurnal Temp Variation**: Amplitude of daily ambient cycles ($\pm 0.0^\circ\text{C}$ to $15.0^\circ\text{C}$).
* **Retarder Delay**: Chemical hydration peak delay ($0$ to $48\text{ hours}$).

---

## 4. Mathematical Formulations & Physics Model

### A. Effective Cementitious Content ($C_{\text{eff}}$)
Accounting for different hydration rates of Supplementary Cementitious Materials (SCMs):
$$C_{\text{eff}} = \text{Cement} + (0.5 \cdot \text{GGBFS}) + (1.2 \cdot \text{Silica Fume})$$

### B. Total Adiabatic Temperature Rise ($dT_{\text{adiab}}$)
Calculated from the heat of hydration, concrete density ($\rho = 2400 \text{ kg/m}^3$), and specific heat ($c$), calibrated with an efficiency factor $\eta = 0.82$ to match baseline trials:
$$dT_{\text{adiab}} = 0.82 \cdot \frac{C_{\text{eff}} \cdot (H_u \cdot 1000)}{\text{Specific Heat} \cdot \text{Density}}$$

### C. Maximum Temperature Rise ($\Delta T_{\text{max}}$)
Thickness correction represents heat trapped due to thermal inertia (mass volume):
$$F_{\text{thickness}} = 1.0 - e^{-0.015 \cdot H}$$
$$\Delta T_{\text{max}} = dT_{\text{adiab}} \cdot F_{\text{thickness}}$$

### D. Transient Cooling Rate ($k_{\text{cooling}}$)
Slabs lose heat over time, scaled by the concrete's actual thermal diffusivity ratio:
$$\alpha_{\text{ratio}} = \frac{K / c}{2.0 / 1000.0}$$
$$k_{\text{cooling}} = \left(0.05 + \frac{25.0}{H}\right) \cdot \alpha_{\text{ratio}}$$

### E. Surface Temperature Transfer ($f_{\text{surface\_transfer}}$)
Determined by surface boundaries and curing methods. Insulation increases the transfer factor, bringing surface temperature closer to the core:
$$f_{\text{surface\_transfer\_base}} = 0.15 + \frac{37.5}{H}$$
$$f_{\text{surface\_transfer}} = 1.0 - (1.0 - f_{\text{surface\_transfer\_base}}) \cdot \text{insulation\_factor}$$

### F. Diurnal Ambient Temp Curve ($T_{\text{ambient}}(t)$)
Models ambient air fluctuations with peak afternoon temperature at 3:00 PM ($t = 0.625\text{ days}$):
$$T_{\text{ambient}}(t) = T_{\text{ambient\_mean}} + T_{\text{amp}} \cdot \cos\left(2\pi \cdot (t - 0.625)\right)$$

### G. Core Temperature Curve ($T_{\text{core}}(t)$)
The core remains isolated from diurnal cycles due to high thermal mass, decaying toward the mean ambient temperature:
$$t_{\text{peak}} = 2.5 + \frac{\text{Retarder Delay (hours)}}{24}$$
$$T_{\text{core}}(t) = T_{\text{ambient\_mean}} + (T_{\text{place}} - T_{\text{ambient\_mean}}) \cdot e^{-k_{\text{cooling}} \cdot t} + \Delta T_{\text{max}} \cdot \left(\frac{t}{t_{\text{peak}}}\right)^{1.8} \cdot e^{1.8 \cdot \left(1 - \frac{t}{t_{\text{peak}}}\right)}$$

### H. Surface Temperature Curve ($T_{\text{surface}}(t)$)
Surface temperatures track the ambient cycle directly:
$$T_{\text{surface}}(t) = T_{\text{ambient}}(t) + f_{\text{surface\_transfer}} \cdot \left(T_{\text{core}}(t) - T_{\text{ambient}}(t)\right)$$

---

## 5. Output Results & Safety Thresholds

The application extracts precise values from the simulated curves to determine design compliance:

1. **Peak Core Temperature**:
   * **Formula**: $\max(T_{\text{core}}(t))$
   * **Compliance Limit**: Must remain **$< 70.0^\circ\text{C}$** by default to prevent Delayed Ettringite Formation (DEF). Under **ACI 201.2R**, this limit is increased up to **$85.0^\circ\text{C}$** if any of the following three exceptions are met:
     * **Exception 1 (Cement Chemistry):** Portland cement conforms to ASTM C150 Type II or V moderate/high sulfate-resisting low-alkali cement ($Na_2O_{eq} \leq 0.60\%$) with limited fineness ($\leq 430\text{ m}^2/\text{kg}$).
     * **Exception 2 (Mortar Strength):** Portland cement conforming to ASTM C150 where the 1-day mortar strength (ASTM C109) does not exceed $20\text{ MPa}$ ($2850\text{ psi}$).
     * **Exception 3 (SCMs / Pozzolans):** Mix uses sufficient pozzolan/SCM levels (slag/GGBFS $\geq 35\%$, silica fume $\geq 5\%$, Class F fly ash $\geq 25\%$, or Class C fly ash $\geq 35\%$).
     * *Note: Temperatures exceeding $85.0^\circ\text{C}$ are strictly prohibited under any circumstances.*
2. **Maximum Core-to-Surface Differential**:
   * **Formula**: $\max(T_{\text{core}}(t) - T_{\text{surface}}(t))$
   * **Compliance Limit**: Must remain **$< 21.0^\circ\text{C}$** (under ACI 207.2R). Exceeding this limit triggers a **High Cracking Risk** warning.
3. **Interactive 14-Day Chart**: Built with Plotly to visualize Core Temp, Surface Temp, Ambient Temp, and the cracking limit line ($T_{\text{surface}} + 21^\circ\text{C}$).
4. **PDF Validation Report**: A 3-page, print-ready document containing:
   * Executive design validation status (PASS/WARNING).
   * Tabular mix parameters and thermal properties.
   * Compliance checklist and signature blocks for Contractor Site Engineer and Lead QA/QC Consultant.
   * Thermal chart and reference documentation.
