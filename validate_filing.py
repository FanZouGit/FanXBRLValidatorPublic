import sys
import os

# Add arelle to the python path
arelle_path = os.path.join(os.path.dirname(__file__), 'Arelle')
if arelle_path not in sys.path:
    sys.path.insert(0, arelle_path)

from arelle import CntlrCmdLine

def validate_edgar_filing(filing_url):
    """
    Validates an EDGAR filing using Arelle.

    :param filing_url: The URL of the filing to validate.
    """
    print(f"Validating {filing_url}...")

    # Remove --logFile, so logging goes to stdout
    args = [
        "--file", filing_url,
        "--plugins", "EDGAR/render",
        "--httpUserAgent", "Arelle via user@example.com",
        "--validate",
        "--disclosureSystem", "efm",
        "--logLevel", "INFO",
        "--logFormat", "[%(messageCode)s] %(message)s"
    ]

    CntlrCmdLine.parseAndRun(args)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sample_filing_url = sys.argv[1]
    else:
        print("Usage: python validate_filing.py <FILING_URL>")
        sys.exit(1)

    validate_edgar_filing(sample_filing_url)
