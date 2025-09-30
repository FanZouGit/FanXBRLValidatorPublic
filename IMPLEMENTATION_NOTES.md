# Implementation Notes

## Summary

This repository now implements a comprehensive XBRL validation workflow for EDGAR filings using Arelle as the core validation engine with integrated DQCRT (Data Quality Committee Rule Tool) support.

## Key Changes

### 1. Enhanced `validate_filing.py`

The main validation script has been enhanced with:

- **EDGAR Plugin Integration**: Uses the EDGAR/render plugin which provides:
  - SEC-specific EFM (EDGAR Filer Manual) validation rules
  - Integrated DQCRT support via XuleInterface
  - Automatic selection of appropriate rule implementation based on taxonomy version
  
- **DQCRT Rule Control**: Supports enabling/disabling DQC rules via command-line flag:
  - Default behavior: DQC/DQCRT rules are enabled
  - `--no-dqc` flag: Disables DQC rules, only runs EFM validation
  
- **Flexible Input**: Accepts both URLs and local file paths for XBRL/iXBRL filings

### 2. Plugin Architecture

The validator uses two external plugins that are cloned from GitHub:

#### EDGAR Plugin
- **Source**: https://github.com/Arelle/EDGAR
- **Location**: `Arelle/arelle/plugin/EDGAR/`
- **Purpose**: Provides SEC-specific validation and integrated DQCRT support
- **Version**: 3.25.2 (as of implementation)

#### xule Plugin  
- **Source**: https://github.com/xbrlus/xule
- **Location**: `Arelle/arelle/plugin/xule/`
- **Purpose**: Rule engine that powers the DQCRT validation
- **Version**: 3.0.30050 (as of implementation)

**Important**: The EDGAR plugin has built-in DQC/DQCRT support. You do NOT need a separate DQC plugin - it's all integrated via EDGAR's XuleInterface module.

### 3. DQCRT Rule Implementation

The EDGAR plugin automatically selects the appropriate DQC implementation:

- **us-gaap/2025 and newer**: XULE-based DQCRT rules
- **us-gaap/2023-2024**: Python-based DQC rules
- **Earlier versions**: Legacy validation approach

This selection happens automatically based on the filing's taxonomy namespace.

### 4. Automation Scripts

#### `setup_plugins.sh`
An automated setup script that:
- Installs Arelle dependencies
- Clones and configures EDGAR plugin
- Clones and configures xule plugin
- Verifies the installations
- Tests basic functionality

### 5. Documentation

#### `README.md`
Comprehensive documentation covering:
- Overview of the validation workflow
- Setup instructions
- Usage examples
- Plugin architecture details
- DQCRT rules information
- Troubleshooting guide
- Advanced usage options

### 6. Git Configuration

#### `.gitignore`
Excludes external plugins from version control:
- `Arelle/arelle/plugin/EDGAR/`
- `Arelle/arelle/plugin/xule/`

These plugins must be cloned by each user via the setup script.

## Technical Implementation Details

### Command Line Argument Handling

The script uses Python's `argparse` for user-facing arguments and carefully manages `sys.argv` when calling Arelle's command-line interface to avoid argument parsing conflicts.

### DQC Rule Control

DQC rules are controlled via the `dqcRuleFilter` parameter:
- **Enabled** (default): Parameter not specified, all applicable rules run
- **Disabled**: Parameter set to `(?!)` (regex that matches nothing)

Example Arelle command with DQC disabled:
```bash
python arelleCmdLine.py \
  --plugins "EDGAR/render" \
  --parameters "dqcRuleFilter=(?!)" \
  --validate \
  --disclosureSystem efm \
  --file <filing>
```

### Plugin Compatibility

The EDGAR plugin explicitly checks for incompatible plugins. Specifically:
- Do NOT load `validate/DQC.py` alongside EDGAR plugin
- EDGAR manages DQC rules internally
- Loading both causes a compatibility error

## Testing

The implementation was tested with:
- Local XBRL instance files
- Both DQC-enabled and DQC-disabled modes
- Plugin installation and verification
- Help and argument parsing

## Future Enhancements

Potential improvements for the future:
1. Add support for batch validation of multiple filings
2. Implement custom output formats (JSON, CSV, etc.)
3. Add filtering for specific rule subsets
4. Integrate with CI/CD pipelines
5. Add support for ESEF (European) filings
6. Create Docker container for consistent environment

## References

- [Arelle Documentation](https://arelle.readthedocs.io/)
- [EDGAR Plugin Repository](https://github.com/Arelle/EDGAR)
- [XULE Plugin Repository](https://github.com/xbrlus/xule)
- [DQC Rules Documentation](https://xbrl.us/dqc-rules/)
- [SEC EDGAR System](https://www.sec.gov/edgar)
- [EDGAR Filer Manual](https://www.sec.gov/info/edgar/edgarfm.htm)

## Maintenance Notes

### Updating Plugins

To update to newer versions of the plugins:

```bash
cd Arelle/arelle/plugin/EDGAR
git pull

cd ../xule
git pull
```

### Version Compatibility

- Arelle core should be kept in sync with SEC's version (currently 2.37.37)
- xule plugin should be kept in sync with SEC's version (currently 30048)
- DQC rule sets are versioned (V27 as of this implementation)

### Support Contacts

- **EDGAR Plugin Issues**: Contact SEC at StructuredData@sec.gov
- **xule/DQC Issues**: Contact XBRL US at info@xbrl.us
- **Arelle Core Issues**: https://github.com/Arelle/Arelle/issues
