"""
Production readiness checker and configuration validator
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv

# Terminal colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
ENDC = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{BOLD}{'=' * 60}{ENDC}")
    print(f"{BLUE}{BOLD}{text:^60}{ENDC}")
    print(f"{BLUE}{BOLD}{'=' * 60}{ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{ENDC}")


def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check if all required environment variables are set"""
    print_header("Checking Environment Variables")
    
    required_vars = {
        'HF_API_TOKEN': 'HuggingFace API token (critical)',
    }
    
    optional_vars = {
        'DEBUG': 'Debug mode (should be False in production)',
        'ALLOWED_ORIGINS': 'CORS allowed origins',
        'FB_PAGE_ID': 'Facebook Page ID (for social sharing)',
        'FB_PAGE_ACCESS_TOKEN': 'Facebook access token',
        'IMGUR_CLIENT_ID': 'Imgur client ID',
    }
    
    errors = []
    warnings = []
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"{var} is not set - {description}")
            print_error(f"{var}: Not set")
        elif var == 'HF_API_TOKEN' and len(value) < 20:
            errors.append(f"{var} seems invalid (too short)")
            print_error(f"{var}: Invalid format")
        else:
            print_success(f"{var}: Set")
    
    # Check optional but important variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if not value:
            warnings.append(f"{var} not set - {description}")
            print_warning(f"{var}: Not set (optional)")
        else:
            print_success(f"{var}: Set")
    
    # Check debug mode
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    if debug:
        errors.append(
            "DEBUG is True - this is a security risk in production!"
        )
        print_error("DEBUG: Enabled (SECURITY RISK)")
    else:
        print_success("DEBUG: Disabled")
    
    return len(errors) == 0, errors + warnings


def check_file_structure() -> Tuple[bool, List[str]]:
    """Check if all required files and directories exist"""
    print_header("Checking File Structure")
    
    required_files = [
        'config.py',
        'app.py',
        'autonomous_artist.py',
        'requirements.txt',
        '.env',
        '.env.example',
        '.gitignore',
    ]
    
    required_dirs = [
        'artist_modules',
        'static',
        'templates',
        'logs',
        'cache',
    ]
    
    errors = []
    
    for file in required_files:
        if Path(file).exists():
            print_success(f"File: {file}")
        else:
            errors.append(f"Missing file: {file}")
            print_error(f"File: {file}")
    
    for directory in required_dirs:
        if Path(directory).exists():
            print_success(f"Directory: {directory}")
        else:
            errors.append(f"Missing directory: {directory}")
            print_error(f"Directory: {directory}")
    
    return len(errors) == 0, errors


def check_security_settings() -> Tuple[bool, List[str]]:
    """Check security-related settings"""
    print_header("Checking Security Configuration")
    
    issues = []
    
    # Check if .env is in .gitignore
    gitignore_path = Path('.gitignore')
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
            if '.env' in gitignore_content:
                print_success(".env is in .gitignore")
            else:
                issues.append(".env should be added to .gitignore")
                print_error(".env not in .gitignore")
    else:
        issues.append("No .gitignore file found")
        print_error("Missing .gitignore")
    
    # Check CORS settings
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
    if allowed_origins == '*':
        issues.append(
            "ALLOWED_ORIGINS is '*' - specify domains in production"
        )
        print_warning("CORS: Allows all origins (not recommended)")
    else:
        print_success(f"CORS: Restricted to {allowed_origins}")
    
    # Check if requirements.txt includes security packages
    req_path = Path('requirements.txt')
    if req_path.exists():
        with open(req_path, 'r') as f:
            reqs = f.read()
            security_packages = [
                'flask-limiter', 'flask-cors', 'flask-talisman'
            ]
            for pkg in security_packages:
                if pkg in reqs:
                    print_success(f"Security package: {pkg}")
                else:
                    issues.append(f"Missing security package: {pkg}")
                    print_error(f"Security package: {pkg}")
    
    return len([i for i in issues if 'should' in i or 'Missing' in i]) == 0,\
        issues


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required Python packages are installed"""
    print_header("Checking Dependencies")
    
    try:
        import flask
        print_success("flask: installed")
    except ImportError:
        print_error("flask: NOT installed")
        return False, ["flask not installed - run: pip install -r "
                      "requirements.txt"]
    
    packages = [
        'flask_limiter',
        'flask_cors',
        'flask_talisman',
        'requests',
        'dotenv',
        'huggingface_hub',
        'PIL',
    ]
    
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
            print_success(f"{pkg}: installed")
        except ImportError:
            missing.append(pkg)
            print_error(f"{pkg}: NOT installed")
    
    if missing:
        return False, [
            f"Missing packages: {', '.join(missing)} - "
            f"run: pip install -r requirements.txt"
        ]
    
    return True, []


def main():
    """Run all production readiness checks"""
    print(f"\n{BOLD}Autonomous Artist - Production Readiness Check{ENDC}")
    print(f"{BOLD}{'=' * 60}{ENDC}")
    
    # Load environment variables
    load_dotenv()
    
    all_checks_passed = True
    all_issues = []
    
    # Run checks
    checks = [
        check_environment_variables,
        check_file_structure,
        check_security_settings,
        check_dependencies,
    ]
    
    for check in checks:
        passed, issues = check()
        all_checks_passed = all_checks_passed and passed
        all_issues.extend(issues)
    
    # Print summary
    print_header("Summary")
    
    if all_checks_passed:
        print_success("All critical checks passed! ✓")
        if all_issues:
            print(f"\n{YELLOW}Warnings:{ENDC}")
            for issue in all_issues:
                print(f"  {YELLOW}⚠{ENDC} {issue}")
    else:
        print_error("Some checks failed! ✗")
        print(f"\n{RED}Errors:{ENDC}")
        for issue in all_issues:
            if any(word in issue for word in [
                'Missing', 'not set', 'should', 'Invalid'
            ]):
                print(f"  {RED}✗{ENDC} {issue}")
            else:
                print(f"  {YELLOW}⚠{ENDC} {issue}")
        print(f"\n{YELLOW}Please fix the issues above before deploying to "
              f"production.{ENDC}")
        sys.exit(1)
    
    print()


if __name__ == "__main__":
    main()
