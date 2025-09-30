import sys
import os

# Add arelle to the python path
arelle_path = os.path.join(os.path.dirname(__file__), 'Arelle')
if arelle_path not in sys.path:
    sys.path.insert(0, arelle_path)

from arelle import CntlrCmdLine

def validate_edgar_filing(filing_url, use_dqc_rules=True):
    """
    Validates an EDGAR filing using Arelle with comprehensive validation workflow.
    
    This function uses Arelle as the core engine with the following plugins:
    1. EDGAR: Provides SEC-specific validation rules and rendering capabilities
    2. xule: A powerful rule engine for custom and advanced validation checks
    3. validate/DQC: Contains the official Data Quality Committee (DQC) rules for US XBRL filings

    :param filing_url: The URL of the filing to validate.
    :param use_dqc_rules: Whether to apply DQC validation rules (default: True)
    """
    print(f"Validating {filing_url}...")
    print(f"Using DQC rules: {use_dqc_rules}")

    # Configure plugins based on validation requirements
    if use_dqc_rules:
        # Use validate/DQC which includes xule engine and DQC rules
        # Also use EDGAR/render for SEC-specific validation and rendering
        plugins = "validate/DQC|EDGAR/render"
    else:
        # Use only EDGAR/render for basic SEC validation
        plugins = "EDGAR/render"

    # Build command line arguments
    args = [
        "--file", filing_url,
        "--plugins", plugins,
        "--httpUserAgent", "Arelle via user@example.com",
        "--validate",
        "--disclosureSystem", "efm",
        "--logLevel", "INFO",
        "--logFormat", "[%(messageCode)s] %(message)s"
    ]

    CntlrCmdLine.parseAndRun(args)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate EDGAR XBRL and iXBRL filings using Arelle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Validation Workflow:
  1. Arelle Engine: Uses arelleCmdLine.py as the core processing engine
  2. EDGAR Plugin: Applies SEC-specific validation rules and resources
  3. xule Plugin: Provides powerful rule engine for advanced validation checks
  4. DQC Rules: Applies Data Quality Committee rules for US XBRL filings

Examples:
  # Validate with full DQC rules (default)
  python validate_filing.py https://www.sec.gov/path/to/filing.htm
  
  # Validate with only EDGAR rules (no DQC)
  python validate_filing.py https://www.sec.gov/path/to/filing.htm --no-dqc
        """
    )
    
    parser.add_argument(
        'filing_url',
        help='URL of the XBRL/iXBRL filing to validate'
    )
    
    parser.add_argument(
        '--no-dqc',
        action='store_true',
        help='Disable DQC validation rules (only use basic EDGAR validation)'
    )
    
    args = parser.parse_args()
    
    validate_edgar_filing(args.filing_url, use_dqc_rules=not args.no_dqc)
