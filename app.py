import os
import sys

# Patch Kaleido tool startup wrapper for directories containing spaces
def patch_kaleido():
    try:
        import kaleido
        base_dir = os.path.dirname(kaleido.__file__)
        executable_path = os.path.join(base_dir, "executable", "kaleido")
        if os.path.exists(executable_path):
            with open(executable_path, "r") as f:
                content = f.read()
            modified = False
            if 'cd $DIR' in content:
                content = content.replace('cd $DIR', 'cd "$DIR"')
                modified = True
            if './bin/kaleido $@' in content:
                content = content.replace('./bin/kaleido $@', './bin/kaleido "$@"')
                modified = True
            if modified:
                with open(executable_path, "w") as f:
                    f.write(content)
    except Exception as e:
        pass

patch_kaleido()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
from PIL import Image
from fpdf import FPDF
from datetime import datetime

# Set Page Config with a professional title and layout
st.set_page_config(
    page_title="Burj Nawas - Concrete Thermal Simulation",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- UNIFIED PLOTTING UTILITY -----------------
def generate_thermal_chart(
    placement_temp,
    ambient_temp,
    raft_thickness,
    max_temp_rise,
    core_warning,
    is_dark=True
):
    days = np.linspace(0, 14, 250)
    t_peak = 2.5
    shape_factor = 1.8

    k_cooling = 0.05 + 25.0 / raft_thickness
    f_surface_transfer = 0.15 + 37.5 / raft_thickness

    # Core temp curve equation
    core_temp_curve = (
        ambient_temp +
        (placement_temp - ambient_temp) * np.exp(-k_cooling * days) +
        max_temp_rise * (days / t_peak) ** shape_factor * np.exp(shape_factor * (1 - days / t_peak))
    )

    # Surface Temperature curve
    surface_temp_curve = ambient_temp + f_surface_transfer * (core_temp_curve - ambient_temp)

    # Flat Ambient Temperature
    ambient_curve = np.full_like(days, ambient_temp)

    # Dotted 21°C Differential Limit Line (Surface Temp + 21°C)
    differential_limit_curve = surface_temp_curve + 21.0

    # Build Plotly Chart
    fig = go.Figure()

    # Colors
    if is_dark:
        bg_color = '#090d13'
        grid_color = '#1f2937'
        text_color = '#8b949e'
        ambient_color = '#8b949e'
        surface_color = '#58a6ff'
        core_color = '#ff7b72' if core_warning else '#e8bc91'
        limit_color = '#f85149'
        legend_bg = 'rgba(15, 20, 28, 0.85)'
        legend_border = '#1f2937'
        title_color = '#ffffff'
    else:
        # Light theme colors for PDF
        bg_color = '#ffffff'
        grid_color = '#e2e8f0'
        text_color = '#475569'
        ambient_color = '#64748b'
        surface_color = '#0284c7'
        core_color = '#ef4444' if core_warning else '#f97316'
        limit_color = '#dc2626'
        legend_bg = 'rgba(255, 255, 255, 0.85)'
        legend_border = '#cbd5e1'
        title_color = '#0f172a'

    # Ambient line
    fig.add_trace(go.Scatter(
        x=days, y=ambient_curve,
        mode='lines',
        name='Ambient/Air Temp',
        line=dict(color=ambient_color, width=2, dash='dash')
    ))

    # Surface Temp line
    fig.add_trace(go.Scatter(
        x=days, y=surface_temp_curve,
        mode='lines',
        name='Estimated Surface Temp',
        line=dict(color=surface_color, width=3)
    ))

    # Core Temp line
    fig.add_trace(go.Scatter(
        x=days, y=core_temp_curve,
        mode='lines',
        name='Estimated Core Temp',
        line=dict(color=core_color, width=4)
    ))

    # Cracking limit (Surface + 21°C)
    fig.add_trace(go.Scatter(
        x=days, y=differential_limit_curve,
        mode='lines',
        name='Cracking Limit (Surface + 21°C)',
        line=dict(color=limit_color, width=2, dash='dot')
    ))

    # Chart Styling
    fig.update_layout(
        title=dict(
            text="<b>14-Day Thermal Evolution Analysis</b>",
            font=dict(size=18, family="Outfit, sans-serif", color=title_color)
        ),
        xaxis=dict(
            title="Time (Days)",
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            title_font=dict(color=text_color),
            tickfont=dict(color=text_color)
        ),
        yaxis=dict(
            title="Temperature (°C)",
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            title_font=dict(color=text_color),
            tickfont=dict(color=text_color)
        ),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        legend=dict(
            font=dict(color=text_color),
            bgcolor=legend_bg,
            bordercolor=legend_border,
            borderwidth=1,
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode='x unified',
        height=500
    )
    return fig

# ----------------- MATPLOTLIB FALLBACK PLOTTING UTILITY -----------------
def generate_thermal_chart_matplotlib(
    placement_temp,
    ambient_temp,
    raft_thickness,
    max_temp_rise,
    core_warning
):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import io
    
    days = np.linspace(0, 14, 250)
    t_peak = 2.5
    shape_factor = 1.8

    k_cooling = 0.05 + 25.0 / raft_thickness
    f_surface_transfer = 0.15 + 37.5 / raft_thickness

    # Core temp curve equation
    core_temp_curve = (
        ambient_temp +
        (placement_temp - ambient_temp) * np.exp(-k_cooling * days) +
        max_temp_rise * (days / t_peak) ** shape_factor * np.exp(shape_factor * (1 - days / t_peak))
    )

    # Surface Temperature curve
    surface_temp_curve = ambient_temp + f_surface_transfer * (core_temp_curve - ambient_temp)

    # Flat Ambient Temperature
    ambient_curve = np.full_like(days, ambient_temp)

    # Dotted 21°C Differential Limit Line (Surface Temp + 21°C)
    differential_limit_curve = surface_temp_curve + 21.0

    # Build Matplotlib Chart
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
    
    # Styling to match the PDF light theme
    ax.set_facecolor('#ffffff')
    fig.patch.set_facecolor('#ffffff')
    
    # Hide top/right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    
    # Grid lines
    ax.grid(True, linestyle=':', color='#cbd5e1', alpha=0.7)
    
    # Plot curves
    ax.plot(days, ambient_curve, label='Ambient/Air Temp', color='#64748b', linewidth=1.5, linestyle='--')
    ax.plot(days, surface_temp_curve, label='Estimated Surface Temp', color='#0284c7', linewidth=2)
    
    core_color = '#ef4444' if core_warning else '#f97316'
    ax.plot(days, core_temp_curve, label='Estimated Core Temp', color=core_color, linewidth=2.5)
    
    ax.plot(days, differential_limit_curve, label='Cracking Limit (Surface + 21°C)', color='#dc2626', linewidth=1.5, linestyle=':')
    
    # Titles & Labels
    ax.set_title("14-Day Thermal Evolution Analysis", fontsize=12, fontweight='bold', pad=12, color='#0f172a')
    ax.set_xlabel("Time (Days)", fontsize=10, labelpad=8, color='#475569')
    ax.set_ylabel("Temperature (°C)", fontsize=10, labelpad=8, color='#475569')
    
    # Tick colors
    ax.tick_params(colors='#475569', labelsize=9)
    
    # Legend
    legend = ax.legend(loc='upper right', frameon=True, fontsize=8)
    frame = legend.get_frame()
    frame.set_facecolor('#ffffff')
    frame.set_edgecolor('#cbd5e1')
    frame.set_alpha(0.85)
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, facecolor='#ffffff')
    plt.close(fig)
    buf.seek(0)
    return buf.read()

# ----------------- PDF REPORT GENERATOR CLASS -----------------
class ConcretePDFReport(FPDF):
    def header(self):
        # Header block
        self.set_fill_color(15, 20, 28) # deep slate blue
        self.rect(0, 0, 210, 35, 'F')
        
        # Burj Nawas title in sand-gold
        self.set_y(10)
        self.set_x(15)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(220, 168, 116) # #dca874 sand-gold
        self.cell(0, 10, "BURJ NAWAS", new_x="LMARGIN", new_y="NEXT", align="L")
        
        # Subtitle
        self.set_x(15)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(180, 180, 180)
        self.cell(0, 5, "Mass Concrete Thermal Analysis Report (ACI 207)", new_x="LMARGIN", new_y="NEXT", align="L")
        
        # Line break
        self.set_y(35)
        self.ln(10)
        
    def footer(self):
        # Footer block
        self.set_y(-25)
        # Line separator
        self.set_draw_color(220, 168, 116)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        
        # Try to embed the Enki Tech logo on the left side of the PDF footer
        logo_path = "rss/enkitech-logo.png"
        logo_loaded = False
        if os.path.exists(logo_path):
            try:
                # Place logo on the left side of the footer line
                self.image(logo_path, x=15, y=self.get_y() + 1, h=8)
                logo_loaded = True
            except Exception as e:
                pass
        
        # Report sign-off placeholders
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        
        # Adjust text alignment if logo is present
        text_x = 38 if logo_loaded else 15
        self.set_x(text_x)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Developed by Enki Tech  |  www.enki-tech.io", new_x="RIGHT", new_y="TOP", align="L")
        
        self.set_x(15)
        self.cell(0, 10, f"Page {self.page_no()}", new_x="LMARGIN", new_y="NEXT", align="R")

@st.cache_data
def build_pdf_report(
    placement_temp,
    ambient_temp,
    cement,
    ggbfs,
    silica,
    thickness,
    effective_cement,
    f_thickness,
    max_temp_rise,
    peak_core,
    max_diff,
    core_warn,
    diff_warn
):
    # Set margins first so they apply to all pages
    pdf = ConcretePDFReport()
    pdf.set_margins(15, 35, 15)
    pdf.add_page()
    
    # 1. Project metadata block
    pdf.set_y(40)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(0, 10, "1. Executive Curing Validation Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # Validation status banner in PDF
    status_text = "PASS - Mix Design Validated"
    banner_bg = (220, 245, 225) # soft green
    banner_fg = (35, 120, 50)
    
    if core_warn or diff_warn:
        status_text = "WARNING - High Curing Risk Detected"
        banner_bg = (255, 230, 230) # soft red
        banner_fg = (200, 30, 30)
        
    pdf.set_fill_color(*banner_bg)
    pdf.set_text_color(*banner_fg)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"  STATUS: {status_text}", border=True, new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(5)
    
    # Description paragraph
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 10)
    desc = (
        f"This report presents the early-age curing thermal validation for the Burj Nawas raft foundation, "
        f"modeled with a slab thickness of {thickness} cm ({thickness/100:.2f} meters). "
        f"The calculations follow the guidelines set out in ACI 207.1R for mass concrete thermal management."
    )
    pdf.multi_cell(0, 5, desc)
    pdf.ln(5)
    
    # 2. Parameters table (Inputs and Outputs)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(0, 8, "2. Mix Design & Environmental Parameters", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(100, 7, "Parameter Description", border=True, align="L", fill=True)
    pdf.cell(40, 7, "Value", border=True, align="C", fill=True)
    pdf.cell(40, 7, "Unit", border=True, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    # Table Rows
    pdf.set_font("Helvetica", "", 10)
    rows = [
        ("Concrete Placement Temperature (T_place)", f"{placement_temp:.1f}", "°C"),
        ("Ambient Curing / Surface Temp (T_amb)", f"{ambient_temp:.1f}", "°C"),
        ("Cement Content", f"{cement:.0f}", "kg/m³"),
        ("GGBFS (Slag) Content", f"{ggbfs:.0f}", "kg/m³"),
        ("Silica Fume Content", f"{silica:.0f}", "kg/m³"),
        ("Foundation Slab Thickness (H)", f"{thickness:.0f}", "cm"),
    ]
    for desc_row, val, unit in rows:
        pdf.cell(100, 7, f" {desc_row}", border=True)
        pdf.cell(40, 7, val, border=True, align="C")
        pdf.cell(40, 7, unit, border=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # 3. Calculations section
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(0, 8, "3. Thermal Calculations & Intermediate Math", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Effective Cement
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(70, 5, "Effective Cementitious (C_eff):", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(35, 5, f"{effective_cement:.1f} kg/m³", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "  Formula: Cement + 0.5 * GGBFS + 1.2 * Silica", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Thickness Factor
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(70, 5, "Thickness Correction Factor (F_thickness):", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(35, 5, f"{f_thickness:.4f}", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "  Formula: 1.0 - exp(-0.015 * Thickness)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Max Temperature Rise
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(70, 5, "Max Adiabatic Temp Rise (dT_max):", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(35, 5, f"{max_temp_rise:.1f} °C", new_x="RIGHT", new_y="TOP")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "  Formula: (C_eff / 100) * 12.0 * F_thickness", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    # 4. Compliance Check
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(0, 8, "4. Critical Limit Compliance Checks", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(60, 7, "Metric Checked", border=True, fill=True)
    pdf.cell(40, 7, "ACI Limit", border=True, align="C", fill=True)
    pdf.cell(40, 7, "Estimated Value", border=True, align="C", fill=True)
    pdf.cell(40, 7, "Status", border=True, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    # Row 1: DEF
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(60, 7, " Peak Core Temperature", border=True)
    pdf.cell(40, 7, "< 70.0 °C", border=True, align="C")
    pdf.cell(40, 7, f"{peak_core:.1f} °C", border=True, align="C")
    status_def = "PASS" if not core_warn else "FAIL (Risk of DEF)"
    pdf.set_font("Helvetica", "B", 10)
    
    # Explicit statements instead of expressions to avoid Streamlit Magic st.write injection
    if not core_warn:
        pdf.set_text_color(35, 120, 50)
    else:
        pdf.set_text_color(200, 30, 30)
        
    pdf.cell(40, 7, status_def, border=True, align="C", new_x="LMARGIN", new_y="NEXT")
    
    # Row 2: Cracking
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(60, 7, " Core-to-Surface Differential", border=True)
    pdf.cell(40, 7, "< 21.0 °C", border=True, align="C")
    pdf.cell(40, 7, f"{max_diff:.1f} °C", border=True, align="C")
    status_diff = "PASS" if not diff_warn else "FAIL (Cracking Risk)"
    pdf.set_font("Helvetica", "B", 10)
    
    # Explicit statements instead of expressions to avoid Streamlit Magic st.write injection
    if not diff_warn:
        pdf.set_text_color(35, 120, 50)
    else:
        pdf.set_text_color(200, 30, 30)
        
    pdf.cell(40, 7, status_diff, border=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Sign-off Area
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(90, 5, "Calculated By:", new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 5, "Reviewed & Approved By:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 5, "_____________________________", new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 5, "_____________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(90, 4, "EnkiTech Project Engineer", new_x="RIGHT", new_y="TOP")
    pdf.cell(90, 4, "Burj Nawas Lead QA/QC Engineer", new_x="LMARGIN", new_y="NEXT")
    
    # Generate light-themed chart for PDF
    fig_light = generate_thermal_chart(
        placement_temp=placement_temp,
        ambient_temp=ambient_temp,
        raft_thickness=thickness,
        max_temp_rise=max_temp_rise,
        core_warning=core_warn,
        is_dark=False
    )
    
    # Export Plotly Figure to image bytes using Kaleido (fallback to Matplotlib if Kaleido fails)
    chart_img_bytes = None
    try:
        chart_img_bytes = fig_light.to_image(format="png", width=800, height=450, scale=2)
    except Exception as e_kaleido:
        try:
            chart_img_bytes = generate_thermal_chart_matplotlib(
                placement_temp=placement_temp,
                ambient_temp=ambient_temp,
                raft_thickness=thickness,
                max_temp_rise=max_temp_rise,
                core_warning=core_warn
            )
        except Exception as e_matplotlib:
            pass
        
    # Page 2: Visualization and References
    pdf.add_page()
    pdf.set_y(40)
    
    # 5. 14-Day Thermal Evolution Analysis
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(0, 8, "5. 14-Day Thermal Evolution Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # Insert Chart
    if chart_img_bytes:
        try:
            import io
            chart_img = Image.open(io.BytesIO(chart_img_bytes))
            # Page width is 210mm. Margins are 15mm left and right, leaving 180mm printable width.
            # We place the chart with width 180mm.
            pdf.image(chart_img, x=15, y=pdf.get_y(), w=180)
            # Advance y-position (height is 180 * 450 / 800 = 101.25mm)
            pdf.set_y(pdf.get_y() + 105)
        except Exception as e:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(200, 30, 30)
            pdf.cell(0, 8, f"Error rendering chart: {str(e)}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(200, 30, 30)
        pdf.cell(0, 8, "Warning: Simulation chart could not be generated.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
            
    # 6. Engineering References & ACI 207 Methodology
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 20, 28)
    pdf.cell(0, 8, "6. Engineering References & ACI 207 Methodology", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # References text block
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    
    ref_desc = (
        "Mass concrete structural components like raft foundations are subject to high volume change "
        "and thermal stress during hydration. Under ACI 207.1R ('Guide to Mass Concrete'), the early-age "
        "temperature rise is modeled using adiabatic hydration rates adjusted for cementitious composition and member thickness."
    )
    pdf.multi_cell(0, 5, ref_desc)
    pdf.ln(3)
    
    # Bullet points
    bullets = [
        ("Effective Cementitious Content (C_eff):", "Calculated as Cement + 0.5 * GGBFS + 1.2 * Silica Fume. Slag (GGBFS) reduces early thermal load by half (0.5), while highly reactive Silica Fume contributes an exothermic factor of 1.2."),
        ("Thickness & Thermal Inertia:", "Slabs thicker than 2.0 meters (200 cm) trap nearly 100% of their heat of hydration internally (approaching adiabatic conditions). As thickness increases, the cooling rate drops exponentially."),
        ("Thermal Gradient Cracking:", "Rapid cooling of outer concrete faces creates a differential between the core and surface. ACI guidelines set the cracking limit threshold at 21.0 °C to prevent thermal cracking."),
        ("Delayed Ettringite Formation (DEF):", "Exceeding 70.0 °C inside core concrete damages hydration products, causing expansion and micro-cracking when moisture penetrates the structure over time.")
    ]
    
    for title, desc in bullets:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 20, 28)
        pdf.cell(65, 5, f" - {title}", new_x="RIGHT", new_y="TOP")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        # Printable width is 180mm. 65mm is used by the bullet title. So we have 115mm left.
        pdf.multi_cell(115, 5, desc, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        
    # Return PDF bytes
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)


# ----------------- CUSTOM DARK MODE & GREEN SIDEBAR CSS -----------------
# App Background: Deep Slate-Black (#090d13), Sidebar: Green (#1a6563), Sidebar text: Peach-Gold (#e8bc91)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
    
    /* Global Page Overrides */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #090d13;
        color: #e6edf3;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(9, 13, 19, 0.8);
        backdrop-filter: blur(12px);
    }
    
    /* Sidebar Overrides - Solid Green Background (#1a6563) */
    [data-testid="stSidebar"] {
        background-color: #1a6563;
        border-right: 1px solid #144e4c;
    }
    
    /* Force sidebar labels, spans, and markdown paragraphs to be Peach-Gold (#e8bc91) */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stWidgetLabel p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6 {
        color: #e8bc91 !important;
    }
    
    /* Custom Peach-Gold Header in Sidebar */
    .sidebar-header {
        font-size: 1.3rem;
        color: #e8bc91 !important;
        font-weight: 700;
        text-align: center;
        letter-spacing: 0.05em;
        margin-top: 10px;
        margin-bottom: 20px;
        font-family: 'Outfit', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        color: #ffffff;
        font-weight: 600;
    }

    /* Premium Custom Cards */
    .metric-card {
        background: #121820;
        border: 1px solid #222d3d;
        border-radius: 14px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #e8bc91;
        box-shadow: 0 12px 28px rgba(232, 188, 145, 0.15);
    }
    
    .metric-card.warning-active {
        border-color: #ff7b72;
        background: rgba(248, 81, 73, 0.03);
    }
    
    .metric-card.warning-active:hover {
        box-shadow: 0 12px 28px rgba(248, 81, 73, 0.15);
    }
    
    .metric-card.success-active {
        border-color: #3fb950;
        background: rgba(63, 185, 80, 0.03);
    }
    
    .metric-card.success-active:hover {
        box-shadow: 0 12px 28px rgba(63, 185, 80, 0.12);
    }
    
    .metric-card .title {
        font-size: 13px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    .metric-card .value {
        font-size: 38px;
        font-weight: 700;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-card .unit {
        font-size: 16px;
        color: #e8bc91;
        margin-left: 3px;
        font-weight: 600;
    }
    
    /* Styled alert banners */
    .alert-banner {
        padding: 18px;
        border-radius: 10px;
        margin-bottom: 24px;
        font-size: 14.5px;
        line-height: 1.6;
        border-left: 6px solid;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    
    .alert-danger {
        background-color: rgba(248, 81, 73, 0.08);
        color: #ff7b72;
        border-color: #f85149;
    }
    
    .alert-success {
        background-color: rgba(63, 185, 80, 0.08);
        color: #56d364;
        border-color: #3fb950;
    }
    
    /* Technical Reference Card */
    .ref-card {
        background-color: #0f141c;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 24px;
        margin-top: 30px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR HEADER & LOGO -----------------
logo_path = "logo.png"
if os.path.exists(logo_path):
    try:
        logo_img = Image.open(logo_path)
        st.sidebar.image(logo_img, use_container_width=True)
    except Exception as e:
        st.sidebar.markdown(f"<div class='sidebar-header'>BURJ NAWAS</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"<div class='sidebar-header'>BURJ NAWAS</div>", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border-color: #144e4c; margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# ----------------- SIDEBAR INPUTS -----------------
st.sidebar.markdown("<h3 style='color: #e8bc91; font-size: 15px; text-transform: uppercase; letter-spacing: 0.05em;'>Simulation Controls</h3>", unsafe_allow_html=True)

placement_temp = st.sidebar.slider(
    "Placement Temperature (T_place, °C)",
    min_value=10.0,
    max_value=45.0,
    value=25.0,
    step=0.5,
    help="Initial temperature of the concrete immediately after batching and pouring."
)

ambient_temp = st.sidebar.slider(
    "Ambient / Surface Temp (T_amb, °C)",
    min_value=10.0,
    max_value=50.0,
    value=30.0,
    step=0.5,
    help="Average expected ambient temperature during the first 14 days of curing."
)

cement = st.sidebar.number_input(
    "Cement Content (kg/m³)",
    min_value=50,
    max_value=600,
    value=220,
    step=5,
    help="Portland Cement content per cubic meter."
)

ggbfs = st.sidebar.number_input(
    "GGBFS (Slag) Content (kg/m³)",
    min_value=0,
    max_value=400,
    value=180,
    step=5,
    help="Ground Granulated Blast-Furnace Slag content per cubic meter."
)

silica = st.sidebar.number_input(
    "Silica Content (kg/m³)",
    min_value=0,
    max_value=100,
    value=20,
    step=5,
    help="Silica Fume content per cubic meter."
)

raft_thickness = st.sidebar.slider(
    "Raft Thickness (H, cm)",
    min_value=50,
    max_value=500,
    value=250,
    step=10,
    help="Thickness of the raft foundation slab in centimeters. Affects internal heat trapping and cooling rate."
)

# ----------------- CORE LOGIC & MATHEMATICAL CALCULATIONS -----------------
total_cementitious = cement + ggbfs + silica
effective_cement = cement + 0.5 * ggbfs + 1.2 * silica
f_thickness = 1.0 - np.exp(-0.015 * raft_thickness)
max_temp_rise = (effective_cement / 100.0) * 12.0 * f_thickness
peak_core_temp = placement_temp + max_temp_rise
max_differential = peak_core_temp - ambient_temp

# ----------------- SIDEBAR PDF EXPORT FUNCTION -----------------
st.sidebar.markdown("<hr style='border-color: #144e4c; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='color: #e8bc91; font-size: 15px; text-transform: uppercase; letter-spacing: 0.05em;'>Export Options</h3>", unsafe_allow_html=True)

core_warning = peak_core_temp > 70.0
diff_warning = max_differential > 21.0

# Generate PDF report data dynamically
pdf_data = build_pdf_report(
    placement_temp=placement_temp,
    ambient_temp=ambient_temp,
    cement=cement,
    ggbfs=ggbfs,
    silica=silica,
    thickness=raft_thickness,
    effective_cement=effective_cement,
    f_thickness=f_thickness,
    max_temp_rise=max_temp_rise,
    peak_core=peak_core_temp,
    max_diff=max_differential,
    core_warn=core_warning,
    diff_warn=diff_warning
)

# Auto-save PDF report to local workspace folder as a bulletproof backup
pdf_save_status = False
try:
    with open("Burj_Nawas_Thermal_Report.pdf", "wb") as f:
        f.write(pdf_data)
    pdf_save_status = True
except Exception as e:
    pass

if pdf_save_status:
    with open("Burj_Nawas_Thermal_Report.pdf", "rb") as f_pdf:
        pdf_bytes_to_download = f_pdf.read()
    st.sidebar.download_button(
        label="📥 Export PDF Report",
        data=pdf_bytes_to_download,
        file_name=f"Burj_Nawas_Thermal_Report_{raft_thickness}cm.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.sidebar.download_button(
        label="📥 Export PDF Report",
        data=pdf_data,
        file_name=f"Burj_Nawas_Thermal_Report_{raft_thickness}cm.pdf",
        mime="application/pdf",
        use_container_width=True
    )

if pdf_save_status:
    st.sidebar.markdown("<p style='font-size: 11.5px; color: #e8bc91; margin-top: 8px; text-align: center; font-style: italic;'>📄 Auto-saved to project directory!</p>", unsafe_allow_html=True)

# ----------------- MAIN PANEL LAYOUT -----------------
st.markdown("<h1 style='color: #ffffff; margin-bottom: 5px; font-family: Outfit, sans-serif;'>BURJ NAWAS</h1>", unsafe_allow_html=True)
st.markdown(f"<h4 style='color: #e8bc91; font-weight: normal; margin-bottom: 25px;'>Mass Concrete Thermal Simulation &bull; {raft_thickness/100:.2f}m Raft Foundation</h4>", unsafe_allow_html=True)

# Three big metrics columns at the top
col1, col2, col3 = st.columns(3)

with col1:
    card_class = "warning-active" if core_warning else "success-active"
    st.markdown(f"""
        <div class="metric-card {card_class}">
            <div class="title">Peak Core Temp</div>
            <div class="value">{peak_core_temp:.1f}<span class="unit">°C</span></div>
            <div class="title" style="margin-top: 8px; font-size: 10.5px; color: #8b949e;">DEF Limit: 70.0°C</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    card_class = "warning-active" if diff_warning else "success-active"
    st.markdown(f"""
        <div class="metric-card {card_class}">
            <div class="title">Max Temp Differential</div>
            <div class="value">{max_differential:.1f}<span class="unit">°C</span></div>
            <div class="title" style="margin-top: 8px; font-size: 10.5px; color: #8b949e;">Cracking Limit: 21.0°C</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="title">Effective Cement</div>
            <div class="value">{effective_cement:.1f}<span class="unit">kg/m³</span></div>
            <div class="title" style="margin-top: 8px; font-size: 10.5px; color: #8b949e;">Thickness Factor: {f_thickness:.3f}</div>
        </div>
    """, unsafe_allow_html=True)

# ----------------- CONDITIONAL WARNINGS -----------------
alerts_triggered = False

if diff_warning:
    alerts_triggered = True
    st.markdown(
        f"""
        <div class="alert-banner alert-danger">
            <strong>⚠️ High Cracking Risk (Thermal Differential Exceeded):</strong><br>
            The calculated maximum differential is <strong>{max_differential:.1f}°C</strong>, which exceeds the ACI limit of <strong>21°C</strong>.
            Tensile stresses caused by the core-to-surface thermal gradient may trigger structural thermal cracking.
            <br><em>Mitigation: Increase GGBFS replacement, lower the placement temperature (e.g. using chilled water/ice), or apply surface insulation.</em>
        </div>
        """,
        unsafe_allow_html=True
    )

if core_warning:
    alerts_triggered = True
    st.markdown(
        f"""
        <div class="alert-banner alert-danger">
            <strong>❌ Delayed Ettringite Formation (DEF) Risk:</strong><br>
            The estimated peak core temperature is <strong>{peak_core_temp:.1f}°C</strong>, which exceeds the critical threshold of <strong>70°C</strong>.
            Temperatures above this level can permanently alter concrete chemistry, preventing standard ettringite formation and causing expansive cracking in service.
            <br><em>Mitigation: Implement nitrogen pre-cooling, reduce total cement content, or use a high-volume slag design.</em>
        </div>
        """,
        unsafe_allow_html=True
    )

if not alerts_triggered:
    st.markdown(
        """
        <div class="alert-banner alert-success">
            <strong>✅ Design Validated:</strong><br>
            Both peak core temperature (under 70°C) and core-to-surface thermal differential (under 21°C) are within safe design limits. This mix is cleared for the Burj Nawas raft foundation under the specified thickness and environmental conditions.
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------- DATA VISUALIZATION (PLOTLY 14-DAY SIMULATION) -----------------
fig = generate_thermal_chart(
    placement_temp=placement_temp,
    ambient_temp=ambient_temp,
    raft_thickness=raft_thickness,
    max_temp_rise=max_temp_rise,
    core_warning=core_warning,
    is_dark=True
)

# Display Plotly Chart
st.plotly_chart(fig, use_container_width=True)

# ----------------- REFERENCE & DOCUMENTATION -----------------
st.markdown(fr"""
    <div class="ref-card">
        <h4 style="margin-top: 0; color: #e8bc91; font-family: Outfit, sans-serif;">📘 Engineering References & ACI 207 Methodology</h4>
        <p style="font-size: 13.5px; color: #8b949e; line-height: 1.6;">
            Mass concrete structural components like the <strong>{raft_thickness/100:.2f}m thick raft foundation of Burj Nawas</strong> are subject to high volume change and thermal stress during hydration. Under <strong>ACI 207.1R ("Guide to Mass Concrete")</strong>, the early-age temperature rise is modeled using adiabatic hydration rates adjusted for cementitious composition and member thickness.
        </p>
        <ul style="font-size: 13px; color: #8b949e; line-height: 1.6; margin-left: 20px;">
            <li><strong>Effective Cementitious Content:</strong> The effective cementitious content ($C_{{eff}}$) is calculated as $Cement + 0.5 \times GGBFS + 1.2 \times Silica\ Fume$. GGBFS (Slag) has a slower hydration rate, reducing the early thermal load by half ($0.5$). Silica Fume is highly reactive and contributes to early strength development, but accelerates early hydration heat, which is modeled with an exothermic contribution factor of $1.2$.</li>
            <li><strong>Thickness & Thermal Inertia:</strong> Slabs thicker than 2.0 meters (200 cm) trap nearly 100% of their heat of hydration internally (approaching adiabatic conditions). As thickness increases, the cooling rate drops exponentially (heat is retained longer), and the surface-to-core differential becomes more severe.</li>
            <li><strong>Thermal Gradient Cracking:</strong> Rapid cooling of outer concrete faces creates a differential between the hot core and cooler surface. ACI guidelines set the cracking limit threshold at <strong>21°C (38°F)</strong> to prevent macro-cracking from severe thermal stress.</li>
            <li><strong>Delayed Ettringite Formation (DEF):</strong> Exceeding <strong>70°C (158°F)</strong> inside core concrete damages hydration products, causing expansion and micro-cracking when moisture penetrates the structure over time.</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# ----------------- FOOTER -----------------
st.markdown("<hr style='border-color: #1f2937; margin-top: 50px; margin-bottom: 20px;'>", unsafe_allow_html=True)

footer_logo_path = "rss/enkitech-logo.png"
logo_base64 = None
if os.path.exists(footer_logo_path):
    try:
        with open(footer_logo_path, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        pass

if logo_base64:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-top: 15px; margin-bottom: 15px;">
            <img src="data:image/png;base64,{logo_base64}" style="height: 48px; width: auto; object-fit: contain;">
            <span style="color: #8b949e; font-size: 13.5px;">
                Developed by <strong>Enki Tech</strong> &bull; 
                <a href="https://www.enki-tech.io" target="_blank" style="color: #e8bc91; text-decoration: none; font-weight: 500;">www.enki-tech.io</a>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div style="color: #8b949e; font-size: 13.5px; margin-top: 15px; margin-bottom: 15px;">
            Developed by <strong>Enki Tech</strong> &bull; 
            <a href="https://www.enki-tech.io" target="_blank" style="color: #e8bc91; text-decoration: none; font-weight: 500;">www.enki-tech.io</a>
        </div>
        """,
        unsafe_allow_html=True
    )
