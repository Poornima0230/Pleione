import subprocess
import sys
import os


# ============================================================
# SIH 26170
# COMPLETE PIPELINE RUNNER
# ============================================================

print("=" * 70)
print("SIH 26170")
print("AI-DRIVEN ANOMALY DETECTION PIPELINE")
print("=" * 70)


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================================
# MODULES
# ============================================================

modules = [

    (
        "MODULE A: ANOMALY DETECTION",
        "src/anomaly_detection.py"
    ),

    (
        "MODULE B: TIME-SERIES DRIFT PREDICTION",
        "src/module_b_drift_predictor.py"
    ),

    (
        "MODULE C: RISK FUSION",
        "src/risk_fusion.py"
    ),

    (
        "MODULE D: EXPLAINABILITY",
        "src/module_D_explainability.py"
    ),

    (
        "MODULE F: VALIDATION",
        "src/module_F_validation.py"
    )

]


# ============================================================
# RUN EACH MODULE
# ============================================================

for module_name, module_path in modules:

    print("\n")
    print("=" * 70)
    print(f"RUNNING {module_name}")
    print("=" * 70)

    full_path = os.path.join(
        BASE_DIR,
        module_path
    )

    # --------------------------------------------------------
    # Check whether module exists
    # --------------------------------------------------------

    if not os.path.exists(full_path):

        print("\nERROR: File not found:")
        print(full_path)

        sys.exit(1)


    # --------------------------------------------------------
    # Run module
    # --------------------------------------------------------

    result = subprocess.run(
        [
            sys.executable,
            full_path
        ],
        cwd=BASE_DIR
    )


    # --------------------------------------------------------
    # Stop if module fails
    # --------------------------------------------------------

    if result.returncode != 0:

        print("\n" + "=" * 70)
        print("PIPELINE STOPPED")
        print("=" * 70)

        print(
            f"\n{module_name} failed."
        )

        print(
            f"Exit code: {result.returncode}"
        )

        sys.exit(
            result.returncode
        )


    print(
        f"\n{module_name} completed successfully."
    )


# ============================================================
# PIPELINE COMPLETE
# ============================================================

print("\n")
print("=" * 70)
print("ALL PIPELINE MODULES COMPLETED")
print("=" * 70)


# ============================================================
# CHECK GENERATED OUTPUTS
# ============================================================

print("\nGenerated outputs:")


outputs = [

    (
        "Module A",
        "data/module_A_anomaly_results.csv"
    ),

    (
        "Module B",
        "data/module_B_drift_predictions.csv"
    ),

    (
        "Module C",
        "data/final_risk_assessment.csv"
    ),

    (
        "Module D",
        "data/module_D_explanations.csv"
    ),

    (
        "Priority Screening",
        "data/priority_screening_list.csv"
    ),

    (
        "Module F",
        "data/module_F_validation_results.csv"
    )

]


for name, output in outputs:

    path = os.path.join(
        BASE_DIR,
        output
    )

    if os.path.exists(path):

        print(
            f"  ✓ {name}: {output}"
        )

    else:

        print(
            f"  ✗ MISSING: {output}"
        )


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n" + "=" * 70)
print("PIPELINE READY")
print("=" * 70)


print(
    "\nTo launch the dashboard:"
)

print(
    "streamlit run src/module_E_dashboard.py"
)