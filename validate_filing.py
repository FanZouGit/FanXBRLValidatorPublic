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
    1. EDGAR/render: Provides SEC-specific validation rules, rendering capabilities,
       and integrated DQCRT (Data Quality Committee Rule Tool) validation
    2. xule: A powerful rule engine that powers the DQC rules (required by EDGAR plugin)
    
    The EDGAR plugin includes built-in DQC/DQCRT rule support and will automatically
    apply the appropriate rules based on the filing's taxonomy version (us-gaap/2025+
    uses XULE implementation, earlier versions use Python implementation).

    :param filing_url: The URL or file path of the filing to validate.
    :param use_dqc_rules: Whether to apply DQC validation rules (default: True).
                         When False, only basic EFM validation is performed.
    """
    print(f"Validating {filing_url}...")
    print(f"DQC rules enabled: {use_dqc_rules}")

    # The EDGAR/render plugin has built-in DQC support via XuleInterface
    # We always use EDGAR/render; DQC is controlled via formula parameters
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
    
    # Control DQC rule execution via formula parameters
    # Note: When not specified, DQC rules run by default
    # To disable, we set the filter to match no rules  
    if not use_dqc_rules:
        # Disable DQC rules by setting dqcRuleFilter to a regex that matches nothing
        # Using "(?!)" which is a negative lookahead that always fails
        args.extend(["--parameters", "dqcRuleFilter=(?!)"])

    # Temporarily replace sys.argv so CntlrCmdLine.parseAndRun uses our args
    original_argv = sys.argv
    try:
        sys.argv = ['arelleCmdLine.py'] + args
        CntlrCmdLine.parseAndRun(args)
    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate EDGAR XBRL and iXBRL filings using Arelle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Validation Workflow:
  1. Arelle Engine: Uses arelleCmdLine.py as the core processing engine
  2. EDGAR Plugin: Applies SEC-specific EFM validation rules and resources
  3. xule Engine: Provides powerful rule engine for advanced validation (integrated)
  4. DQCRT Rules: Data Quality Committee rules automatically applied based on taxonomy
     - us-gaap/2025+: Uses XULE-based DQCRT implementation
     - us-gaap/2023-2024: Uses Python-based DQC implementation
  
Note: The EDGAR plugin has built-in DQCRT (Data Quality Committee Rule Tool) support.
      DQC rules are automatically selected based on the filing's taxonomy version.

Examples:
  # Validate with full DQC/DQCRT rules (default)
  python validate_filing.py https://www.sec.gov/path/to/filing.htm
  
  # Validate with only EFM rules (no DQC/DQCRT)
  python validate_filing.py https://www.sec.gov/path/to/filing.htm --no-dqc
  
  # Validate a local file
  python validate_filing.py /path/to/filing.htm
        """
    )
    
    parser.add_argument(
        'filing_url',
        help='URL or file path of the XBRL/iXBRL filing to validate'
    )
    
    parser.add_argument(
        '--no-dqc',
        action='store_true',
        help='Disable DQC/DQCRT validation rules (only use basic EFM validation)'
    )
    
    args = parser.parse_args()
    
    validate_edgar_filing(args.filing_url, use_dqc_rules=not args.no_dqc)
