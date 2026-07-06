import sys

from colorama import Fore, Style, init

# Initialize colorama for Windows systems cross-compatibility
init(autoreset=True)

ASCII_BANNER = f"""
{Fore.CYAN}{Style.BRIGHT}███████╗███╗   ███╗███████╗████████╗
██╔════╝████╗ ████║██╔════╝╚══██╔══╝
{Fore.BLUE}███████╗██╔████╔██║█████╗     ██║   
╚════██║██║╚██╔╝██║██╔══╝     ██║   
{Fore.MAGENTA}███████║██║ ╚═╝ ██║██║        ██║   
╚══════╝╚═╝     ╚═╝╚═╝        ╚═╝   
 {Fore.WHITE}Social Media Footprinting Tool {Fore.GREEN}v1.0.0{Fore.CYAN}
 {Fore.WHITE}OSINT Digital Footprint Analyzer | Capstone Edition
"""

DISCLAIMER_TEXT = f"""
{Fore.RED}{Style.BRIGHT}================================================================================
                           MANDATORY ETHICAL DISCLAIMER
================================================================================
{Fore.YELLOW}
1. This tool is designed strictly for educational, security auditing, digital
   forensics research, and authorized penetration testing exercises.
2. It performs only passive reconnaissance using public platform URL signatures.
   No authentication bypass, CAPTCHA subversion, or private API scraping is attempted.
3. You must obtain explicit authorization from the target owner before auditing,
   or scan only your own public profiles.
4. The user is entirely responsible for compliance with local and international
   privacy laws, as well as the target platforms' Terms of Service.

{Fore.RED}{Style.BRIGHT}By choosing to proceed, you certify that:
- You have read, understood, and accept these conditions.
- You will use this software responsibly and legally.
================================================================================
"""

FALLBACK_BANNER = f"""
{Fore.CYAN}{Style.BRIGHT}================================================================================
          SMFT -- Social Media Footprinting Tool (v1.0.0)
================================================================================
 {Fore.WHITE}OSINT Digital Footprint Analyzer | Capstone Edition
"""


def print_banner() -> None:
    """Prints the styled ASCII project logo banner."""
    try:
        print(ASCII_BANNER)
    except UnicodeEncodeError:
        try:
            print(FALLBACK_BANNER)
        except Exception:
            # Absolute fallback
            print("SMFT -- Social Media Footprinting Tool v1.0.0")


def print_disclaimer() -> None:
    """Prints the mandatory ethical usage disclaimer screen."""
    try:
        print(DISCLAIMER_TEXT)
    except UnicodeEncodeError:
        # Fallback with safe characters
        safe_text = DISCLAIMER_TEXT.encode(sys.stdout.encoding or "ascii", errors="replace").decode(
            sys.stdout.encoding or "ascii"
        )
        print(safe_text)
