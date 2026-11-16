"""Central configuration, palette tokens, and scientific constants for AMR RADAR."""

APP_TITLE = "AMR RADAR"
APP_FULL_NAME = "Antimicrobial Resistance Monitoring and Analytics Platform"
APP_TAGLINE = "Turning Laboratory Data into Meaningful Surveillance Insights."

# Design Tokens (Black, White, Light Grey, Warm Beige)
COLOR_BLACK = "#111111"
COLOR_CHARCOAL = "#262626"
COLOR_WHITE = "#FFFFFF"
COLOR_CANVAS = "#F3F2EE"
COLOR_STONE = "#EFECE6"
COLOR_BEIGE = "#C8B79F"
COLOR_BEIGE_SOFT = "#EAE3D5"

# Calibrated S/I/R Data Colors
COLOR_SUSCEPTIBLE = "#2E6F5E"
COLOR_INTERMEDIATE = "#B47B2B"
COLOR_RESISTANT = "#A63A3A"

# Required and Expected Columns for Format A (Individual Records)
REQUIRED_INDIVIDUAL_COLUMNS = ["Organism", "Antibiotic", "Result"]
EXPECTED_INDIVIDUAL_COLUMNS = [
    "Sample_ID",
    "Organism",
    "Antibiotic",
    "Result",
    "Date",
    "Location",
    "Laboratory",
    "Standard",
    "Standard_Version",
]

VALID_SIR_VALUES = {"S", "I", "R"}
LOW_SAMPLE_THRESHOLD = 30
VERY_LOW_SAMPLE_THRESHOLD = 10

DISCLAIMER_TEXT = (
    "Research and Public-Health Surveillance Only: AMR RADAR provides retrospective "
    "microbiological analytics and data-quality auditing. It does NOT diagnose patients, "
    "predict individual clinical outcomes, or recommend treatments."
)
