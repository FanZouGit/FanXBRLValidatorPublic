# XBRL Validator for EDGAR Filings

A Python application to validate EDGAR XBRL and iXBRL filings using Arelle as the core validation engine with comprehensive rule sets.

## Overview

This validation application implements a comprehensive workflow for validating SEC XBRL filings:

1. **Arelle Engine**: The main processing is handled by Arelle, which is executed using the `arelleCmdLine.py` script from the `Arelle/` directory.

2. **Input Filing**: The process starts with an XBRL filing (traditional XBRL or inline XBRL/iXBRL format).

3. **Plugins for Validation Logic**: Arelle uses a plugin system to apply different sets of validation rules:
   - **EDGAR/render**: Provides SEC-specific EFM validation rules, rendering capabilities, and integrated DQCRT support
   - **xule**: A powerful rule engine that powers the DQC/DQCRT rules (automatically used by EDGAR plugin)

4. **Validation Execution**: When you run the validator, it:
   - Loads the XBRL filing
   - Applies EFM (EDGAR Filer Manual) validation rules
   - Automatically applies DQCRT (Data Quality Committee Rule Tool) rules based on taxonomy version
   - Generates a validation report

5. **Rendering (Optional)**: The EdgarRenderer plugin can be used to create a human-readable HTML version of the validated data.

## Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/FanZouGit/FanXBRLValidatorPublic.git
   cd FanXBRLValidatorPublic
   ```

2. Install Arelle dependencies:
   ```bash
   cd Arelle
   pip install -r requirements.txt
   cd ..
   ```

3. Install external plugins:
   
   The validator requires two external plugins that need to be cloned into the Arelle plugin directory:
   
   ```bash
   # Navigate to the plugin directory
   cd Arelle/arelle/plugin
   
   # Clone EDGAR plugin
   git clone https://github.com/Arelle/EDGAR.git
   
   # Clone xule plugin (required by EDGAR for DQC rules)
   git clone https://github.com/xbrlus/xule.git
   
   # Move xule engine to proper location
   mv xule/plugin/xule ./xule
   rm -rf xule
   
   # Return to project root
   cd ../../../
   ```
   
   **Or use the automated setup script:**
   
   ```bash
   ./setup_plugins.sh
   ```

## Usage

### Basic Validation

Validate an XBRL filing with full DQC rules (default):

```bash
python validate_filing.py <FILING_URL_OR_PATH>
```

Example:
```bash
python validate_filing.py https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm
```

### Validation Without DQC Rules

If you want to run only basic EFM validation without the comprehensive DQCRT rules:

```bash
python validate_filing.py <FILING_URL_OR_PATH> --no-dqc
```

### Command Line Options

```
usage: validate_filing.py [-h] [--no-dqc] filing_url

Validate EDGAR XBRL and iXBRL filings using Arelle

positional arguments:
  filing_url  URL of the XBRL/iXBRL filing to validate

options:
  -h, --help  show this help message and exit
  --no-dqc    Disable DQC/DQCRT validation rules (only use basic EFM validation)
```

## Validation Workflow

### Plugin Architecture

The validation process uses the following plugin components:

1. **EDGAR Plugin** (`EDGAR/render`)
   - Source: https://github.com/Arelle/EDGAR
   - Provides SEC EDGAR-specific EFM (EDGAR Filer Manual) validation rules
   - Generates traditional and inline XBRL viewers
   - **Includes integrated DQCRT (Data Quality Committee Rule Tool) support**
   - Automatically selects appropriate rule implementation:
     - **us-gaap/2025+**: XULE-based DQCRT rules
     - **us-gaap/2023-2024**: Python-based DQC rules

2. **xule Plugin** (`xule`)
   - Source: https://github.com/xbrlus/xule
   - XBRL rule engine for expressing validation rules
   - Powers the DQCRT rules in EDGAR plugin
   - Supports complex business rule validation
   - Required by EDGAR plugin for DQC functionality

**Note**: The EDGAR plugin has built-in DQC support via its XuleInterface module. You do not need to load a separate DQC plugin - it's all integrated into EDGAR/render.

### Validation Process Flow

```
Filing (XBRL/iXBRL)
    ↓
Arelle Engine (arelleCmdLine.py)
    ↓
EDGAR Plugin (EDGAR/render)
    ├── EFM Validation Rules
    ├── SEC-specific checks
    └── Integrated DQCRT/DQC
        └── xule Engine
            ├── XULE-based DQCRT (us-gaap/2025+)
            └── Python-based DQC (us-gaap/2023-2024)
    ↓
Validation Report
```

## Output

The validator produces output in the following format:

```
[MessageCode] Message text
```

Example output:
```
[info] Activation of plug-in Edgar Renderer successful, version 3.25.2.
[EFM.6.05.20.deiFactsMissing] DEI facts are missing.
[DQC.US.0001.74] Calculations inconsistent with reported values.
[info] validated in 2.34 secs
```

### Understanding Message Codes

- **EFM.x.x.x**: EDGAR Filer Manual validation errors
- **DQC.US.xxxx.xx**: Data Quality Committee rule violations
- **info**: Informational messages
- **warn**: Warning messages
- **error**: Error messages

## DQCRT Rules

The EDGAR plugin includes integrated DQCRT (Data Quality Committee Rule Tool) support, which provides comprehensive quality checks for XBRL filings. 

### Rule Implementation

- **us-gaap/2025 and newer**: XULE-based DQCRT implementation
- **us-gaap/2023-2024**: Python-based DQC implementation
- The appropriate implementation is automatically selected based on the filing's taxonomy

### DQCRT Rules Coverage

The DQCRT rules selected by FASB for 2025 filings include:
- **Calculation consistency**: Ensures reported values match calculated totals
- **Axis and member validation**: Validates dimensional breakdowns
- **Unit consistency**: Checks that monetary amounts use appropriate units
- **Period validation**: Ensures date ranges are logical
- **Extension taxonomy checks**: Validates custom elements
- And many more (60+ rules)

### Specific Rules (2025)

The following DQC rules are included in DQCRT for 2025:
```
0001 0004 0005 0006 0008 0009 0013 0014 0015 0033 0036 0041 0043 0044 0045 0046 
0047 0048 0051 0052 0053 0054 0055 0057 0060 0061 0062_2017 0065 0068 0069 0070 
0071 0072 0073 0076 0077 0078 0079 0084 0085 0089 0090 0091 0095 0098 0099 0108 
0109 0112 0118 0119 0123 0126 0128 0133 0134 0135 0136 0137 0141
```

For a complete list and description of all DQC rules, visit: https://xbrl.us/dqc-rules/

## Troubleshooting

### Plugin Not Found

If you get errors about missing plugins, ensure you've correctly installed the external plugins:

```bash
# Verify EDGAR plugin exists
ls Arelle/arelle/plugin/EDGAR/

# Verify xule plugin exists
ls Arelle/arelle/plugin/xule/

# If missing, run the setup script
./setup_plugins.sh
```

### Network Issues

If you're validating remote URLs and encounter network errors:

1. Check your internet connection
2. Verify the filing URL is correct
3. Some firewalls may block XBRL schema downloads; consider downloading the filing locally first

### Memory Issues

For large filings, you may need to increase Python's memory limits:

```bash
# Linux/Mac
ulimit -s unlimited
python validate_filing.py <filing>

# Or use Python with increased stack size
python -X dev validate_filing.py <filing>
```

## Advanced Usage

### Direct Arelle Usage

You can also use Arelle directly with custom options:

```bash
cd Arelle
python arelleCmdLine.py \
  --plugins "EDGAR/render" \
  --httpUserAgent "Your Company via your.email@example.com" \
  --disclosureSystem efm \
  --validate \
  --file <filing-path-or-url>
```

To disable DQC rules:

```bash
python arelleCmdLine.py \
  --plugins "EDGAR/render" \
  --formulaParamInputValue "dqcRuleFilter=" \
  --httpUserAgent "Your Company via your.email@example.com" \
  --disclosureSystem efm \
  --validate \
  --file <filing-path-or-url>
```

### Custom Plugin Configuration

To use specific plugin configurations, modify the `validate_filing.py` script or use Arelle directly.

## Resources

- [Arelle Documentation](https://arelle.readthedocs.io/)
- [EDGAR Plugin Documentation](https://github.com/Arelle/EDGAR)
- [XULE Plugin Documentation](https://github.com/xbrlus/xule)
- [DQC Rules Documentation](https://xbrl.us/dqc-rules/)
- [SEC EDGAR System](https://www.sec.gov/edgar)

## License

This project uses Arelle and its plugins, which are licensed under Apache License 2.0.

- Arelle: Apache License 2.0
- EDGAR Plugin: Apache License 2.0 (portions by SEC employees not subject to domestic copyright)
- xule Plugin: Apache License 2.0
- DQC Rules: Apache License 2.0

## Support

For issues related to:
- **This validator**: Open an issue on this repository
- **Arelle**: Visit https://arelle.org or https://github.com/Arelle/Arelle
- **EDGAR Plugin**: Contact SEC at StructuredData@sec.gov
- **XULE/DQC**: Contact XBRL US at info@xbrl.us
