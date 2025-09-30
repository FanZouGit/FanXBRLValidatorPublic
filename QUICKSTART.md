# Quick Start Guide

Get started validating EDGAR XBRL filings in 3 easy steps!

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/FanZouGit/FanXBRLValidatorPublic.git
cd FanXBRLValidatorPublic

# Run the automated setup script
./setup_plugins.sh
```

The setup script will:
- Install Arelle dependencies
- Clone EDGAR and xule plugins from GitHub
- Verify the installation

## Step 2: Validate a Filing

```bash
# Validate with full DQC/DQCRT rules (recommended)
python validate_filing.py <filing-url-or-path>

# Example with a real SEC filing
python validate_filing.py https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240629.htm

# Validate with only basic EFM rules (without DQC)
python validate_filing.py <filing-url-or-path> --no-dqc
```

## Step 3: Review Results

The validator will output:
- EFM validation errors (e.g., `[EFM.6.05.20]`)
- DQC rule violations (e.g., `[DQC.US.0001.74]`)
- Informational messages
- Validation summary

### Understanding the Output

```
[EFM.6.03.03] Invalid instance document name, must match "{base}-{yyyymmdd}.xml"
```
- **EFM.x.x.x**: EDGAR Filer Manual rules (SEC-specific)

```
[DQC.US.0001.74] Calculations inconsistent with reported values
```
- **DQC.US.xxxx.xx**: Data Quality Committee rules

```
[info] validated in 2.34 secs
```
- **info/warn/error**: Message severity levels

## Common Use Cases

### Validate Local File
```bash
python validate_filing.py /path/to/local/filing.htm
```

### Validate Remote URL
```bash
python validate_filing.py https://www.sec.gov/path/to/filing.htm
```

### Skip DQC Rules for Faster Validation
```bash
python validate_filing.py <filing> --no-dqc
```

### Get Help
```bash
python validate_filing.py --help
```

## What Gets Validated?

✅ **EFM Rules** (Always)
- File naming conventions
- Required disclosures
- Document structure
- Context validity
- Calculation consistency (basic)

✅ **DQCRT Rules** (When Enabled)
- Advanced calculation checks
- Dimensional validation
- Axis and member consistency
- Period validation
- Extension taxonomy quality
- 60+ additional quality checks

## Troubleshooting

### "Plugin not found" error
Run the setup script again:
```bash
./setup_plugins.sh
```

### Network errors with remote filings
Download the filing locally first, then validate:
```bash
# Download from SEC
wget <filing-url>

# Validate local copy
python validate_filing.py <local-file>
```

### Memory issues with large filings
Use Python 3.8+ and ensure sufficient RAM (4GB+ recommended)

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) for technical details
- Visit [XBRL.US DQC Rules](https://xbrl.us/dqc-rules/) for rule documentation

## Need Help?

- **EDGAR Plugin**: Contact SEC at StructuredData@sec.gov
- **DQC Rules**: Contact XBRL US at info@xbrl.us
- **Arelle**: Visit https://arelle.org
- **This Repository**: Open an issue on GitHub
