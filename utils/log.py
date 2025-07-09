from colorama import Fore, Style, init
from datetime import datetime
import sys
from typing import Optional

# Initialize colorama for Windows compatibility
init()

def information(message: str, print_to_console: bool = True) -> None:
    """
    Log information to the console with blue color.
    
    Args:
        message: The information message to log
        print_to_console: Whether to print to console (default: True)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{Fore.BLUE}[INFO] {timestamp} - {message}{Style.RESET_ALL}"
    
    if print_to_console:
        print(formatted_message)
    
def error(message: str, exception: Optional[Exception] = None, print_to_console: bool = True) -> None:
    """
    Log error to the console with red color.
    
    Args:
        message: The error message to log
        exception: Optional exception object for detailed logging
        print_to_console: Whether to print to console (default: True)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_details = f" - Exception: {str(exception)}" if exception else ""
    formatted_message = f"{Fore.RED}[ERROR] {timestamp} - {message}{error_details}{Style.RESET_ALL}"
    
    if print_to_console:
        print(formatted_message, file=sys.stderr)
    
def success(message: str, print_to_console: bool = True) -> None:
    """
    Log success to the console with green color.
    
    Args:
        message: The success message to log
        print_to_console: Whether to print to console (default: True)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{Fore.GREEN}[SUCCESS] {timestamp} - {message}{Style.RESET_ALL}"
    
    if print_to_console:
        print(formatted_message)

def warning(message: str, print_to_console: bool = True) -> None:
    """
    Log warning to the console with yellow color.
    
    Args:
        message: The warning message to log
        print_to_console: Whether to print to console (default: True)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{Fore.YELLOW}[WARNING] {timestamp} - {message}{Style.RESET_ALL}"
    
    if print_to_console:
        print(formatted_message)
    
