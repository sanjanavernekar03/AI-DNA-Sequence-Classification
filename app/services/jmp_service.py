import os
import sys
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configure JMP output folder under app/static/images/jmp_charts
BASE_DIR = Path(__file__).resolve().parent.parent.parent
JMP_OUTPUT_DIR = BASE_DIR / "app" / "static" / "images" / "jmp_charts"
JMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Default JMP executable path
DEFAULT_JMP_EXE = r"C:\Program Files\JMP\JMP\19\jmp.exe"


def get_jmp_executable() -> Optional[str]:
    """Detect installed JMP executable path safely."""
    custom_path = os.getenv("JMP_EXE_PATH")
    if custom_path and os.path.exists(custom_path):
        return custom_path
    
    if os.path.exists(DEFAULT_JMP_EXE):
        return DEFAULT_JMP_EXE

    # Alternative standard installation paths
    possible_paths = [
        r"C:\Program Files\JMP\JMP\18\jmp.exe",
        r"C:\Program Files\JMP\JMP\17\jmp.exe",
        r"C:\Program Files\SAS\JMP\19\jmp.exe",
        r"C:\Program Files\SAS\JMP\18\jmp.exe",
        r"C:\Program Files (x86)\JMP\JMP\19\jmp.exe"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p

    return None


def generate_jmp_nucleotide_graph(
    a_count: int,
    t_count: int,
    g_count: int,
    c_count: int,
    analysis_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Invokes JMP Student Edition via JSL / Automation to generate a genuine JMP Graph Builder bar chart.
    
    Args:
        a_count: Adenine count
        t_count: Thymine count
        g_count: Guanine count
        c_count: Cytosine count
        analysis_id: Unique analysis identifier for filename scoping
        
    Returns:
        dict: {
            "success": bool,
            "image_path": str (absolute path),
            "relative_url": str (static path for Flask),
            "error": str or None
        }
    """
    # Standardize integer counts
    a_count = int(a_count or 0)
    t_count = int(t_count or 0)
    g_count = int(g_count or 0)
    c_count = int(c_count or 0)

    # Scoped unique suffix incorporating analysis_id AND nucleotide counts to guarantee uniqueness per analysis
    if analysis_id:
        unique_suffix = f"{analysis_id}_a{a_count}_t{t_count}_g{g_count}_c{c_count}"
    else:
        unique_suffix = f"seq_a{a_count}_t{t_count}_g{g_count}_c{c_count}"

    filename = f"jmp_bubble_{unique_suffix}.png"
    output_path = JMP_OUTPUT_DIR / filename
    relative_url = f"images/jmp_charts/{filename}"

    # Return cached image if already generated for these exact metrics & analysis
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"JMP Bubble Plot image already exists for analysis '{analysis_id}': {output_path}")
        return {
            "success": True,
            "image_path": str(output_path),
            "relative_url": relative_url,
            "error": None
        }

    # Format output path for JSL (forward slashes)
    jsl_png_path = str(output_path).replace("\\", "/")

    # JSL Script using dedicated JMP Bubble Plot Platform
    jsl_code = f"""
dt = New Table( "Nucleotide Distribution",
    Add Rows( 4 ),
    New Column( "Nucleotide", Character, "Nominal", Set Values( {{"A", "T", "G", "C"}} ) ),
    New Column( "Count / bp", Numeric, "Continuous", Set Values( [{a_count}, {t_count}, {g_count}, {c_count}] ) )
);

bp = dt << Bubble Plot(
    X( :Nucleotide ),
    Y( :"Count / bp" ),
    Sizes( :"Count / bp" ),
    Coloring( :Nucleotide ),
    Title( "Nucleotide Distribution (bp)" ),
    Show Labels( All )
);

Report( bp ) << Save Picture( "{jsl_png_path}", "png" );
Close( dt, NoSave );
"""

    try:
        # 1. Primary Method: COM Automation via win32com
        import win32com.client
        jmp_app = win32com.client.Dispatch("JMP.Application")
        jmp_app.Visible = False
        jmp_app.RunCommand(jsl_code)

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Dedicated JMP Bubble Plot Platform successfully created graph at: {output_path}")
            return {
                "success": True,
                "image_path": str(output_path),
                "relative_url": relative_url,
                "error": None
            }
    except Exception as com_err:
        logger.warning(f"JMP COM Automation failed: {com_err}. Attempting CLI fallback...")

    # 2. Fallback Method: Run JSL file via JMP Executable Subprocess
    jmp_exe = get_jmp_executable()
    if not jmp_exe:
        err_msg = "JMP Student Edition executable not found on system."
        logger.error(err_msg)
        return {
            "success": False,
            "image_path": None,
            "relative_url": None,
            "error": err_msg
        }

    jsl_file_path = JMP_OUTPUT_DIR / f"temp_script_{unique_suffix}.jsl"
    try:
        with open(jsl_file_path, "w", encoding="utf-8") as f:
            f.write(jsl_code + "\nExit();\n")

        import subprocess
        proc = subprocess.Popen([jmp_exe, str(jsl_file_path)])
        
        # Wait up to 8 seconds for image generation
        import time
        for _ in range(16):
            time.sleep(0.5)
            if output_path.exists() and output_path.stat().st_size > 0:
                break

        try:
            proc.terminate()
        except Exception:
            pass

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"JMP CLI successfully created graph at: {output_path}")
            return {
                "success": True,
                "image_path": str(output_path),
                "relative_url": relative_url,
                "error": None
            }
        else:
            err_msg = "JMP executed but output image was not generated."
            logger.error(err_msg)
            return {
                "success": False,
                "image_path": None,
                "relative_url": None,
                "error": err_msg
            }

    except Exception as sub_err:
        err_msg = f"Failed to execute JMP: {str(sub_err)}"
        logger.error(err_msg)
        return {
            "success": False,
            "image_path": None,
            "relative_url": None,
            "error": err_msg
        }
    finally:
        if jsl_file_path.exists():
            try:
                jsl_file_path.unlink()
            except Exception:
                pass
