#!/usr/bin/env python3
"""
🤖 RASA 3.6.4 Automotive Chatbot Setup - ENHANCED WITH PROGRESS TRACKING
Installs each dependency individually with real-time progress and proper timeouts
"""

import subprocess
import sys
import os
from pathlib import Path
import platform
import time
import threading

def print_colored(message, color='white'):
    """Print colored messages"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    color_code = colors.get(color, colors['white'])
    reset_code = colors['reset']
    print(f"{color_code}{message}{reset_code}")

def animate_progress(stop_event, package_name):
    """Show animated progress while installation is running - Windows safe"""
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        print(f"\r[INSTALLING] {package_name}... {animation[idx % len(animation)]}", end='', flush=True)
        idx += 1
        time.sleep(0.3)

def run_command_with_progress(command, description, timeout=300, show_output=False):
    """Run a command with animated progress and return success status"""
    try:
        print_colored(f"[SETUP] {description}...", 'cyan')
        
        if show_output:
            # For RASA and other large packages, show live output
            print_colored("[OUTPUT] Live installation output (this may take several minutes):", 'blue')
            print_colored("=" * 60, 'blue')
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            start_time = time.time()
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                
                # Check timeout
                if time.time() - start_time > timeout:
                    process.terminate()
                    print_colored(f"[TIMEOUT] {description} - TIMEOUT after {timeout} seconds", 'yellow')
                    return False
            
            return_code = process.poll()
            print_colored("=" * 60, 'blue')
            
        else:
            # For smaller packages, show animated progress
            stop_event = threading.Event()
            progress_thread = threading.Thread(target=animate_progress, args=(stop_event, description))
            progress_thread.start()
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return_code = result.returncode
                
            finally:
                stop_event.set()
                progress_thread.join()
                print()  # New line after progress animation
        
        if return_code == 0:
            print_colored(f"[OK] {description} - SUCCESS", 'green')
            return True
        else:
            print_colored(f"[ERROR] {description} - FAILED (Exit code: {return_code})", 'red')
            return False
            
    except subprocess.TimeoutExpired:
        print_colored(f"[TIMEOUT] {description} - TIMEOUT after {timeout} seconds", 'yellow')
        print_colored(f"[TIP] RASA installation can take 5-10 minutes on slower systems", 'cyan')
        return False
    except Exception as e:
        print_colored(f"[ERROR] {description} - ERROR: {str(e)}", 'red')
        return False

def run_command(command, description, timeout=120):
    """Legacy run_command for backward compatibility"""
    return run_command_with_progress(command, description, timeout, False)

def read_requirements():
    """Read and parse requirements.txt"""
    requirements_file = Path("backend/requirements.txt")
    if not requirements_file.exists():
        print_colored("❌ requirements.txt not found!", 'red')
        return []
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            packages.append(line)
    
    return packages

def install_package_individually(package, timeout=300, show_progress=False):
    """Install a single package with configurable timeout and progress"""
    python_exe = ".venv\\Scripts\\python.exe" if os.name == 'nt' else ".venv/bin/python"
    command = f"{python_exe} -m pip install \"{package}\" --timeout 300 --no-cache-dir"
    
    if show_progress:
        return run_command_with_progress(command, f"Installing {package}", timeout, True)
    else:
        return run_command_with_progress(command, f"Installing {package}", timeout, False)

def estimate_time(package):
    """Estimate installation time for different packages"""
    heavy_packages = ['rasa', 'tensorflow', 'torch', 'transformers', 'spacy']
    medium_packages = ['scipy', 'pandas', 'numpy', 'faiss-cpu']
    
    package_lower = package.lower()
    
    if any(heavy in package_lower for heavy in heavy_packages):
        return "⏱️ 5-10 minutes", 600  # 10 minutes timeout
    elif any(medium in package_lower for medium in medium_packages):
        return "⏱️ 1-3 minutes", 300   # 5 minutes timeout
    else:
        return "⏱️ 30-60 seconds", 120  # 2 minutes timeout

def main():
    print_colored("=" * 60, 'cyan')
    print_colored("[SETUP] RASA 3.6.4 Automotive Chatbot Setup - ENHANCED VERSION", 'cyan')
    print_colored("=" * 60, 'cyan')
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_colored(f"[PYTHON] Python {python_version}", 'blue')
    
    if sys.version_info < (3, 9):
        print_colored("[ERROR] Python 3.9+ required for this setup", 'red')
        return
    
    print_colored("[OK] Perfect! Python 3.9+ - compatible versions", 'green')
    
    # Check virtual environment
    if not os.path.exists('.venv'):
        print_colored("[ERROR] Virtual environment not found! Please create .venv first", 'red')
        return
    
    print_colored("[INFO] Virtual environment exists", 'blue')
    
    # Upgrade pip
    if not run_command(".venv\\Scripts\\python.exe -m pip install --upgrade pip", "Upgrading pip"):
        print_colored("[WARN] Pip upgrade failed, continuing anyway...", 'yellow')
    
    # Install RASA core first with proper timeout and progress
    print_colored("[STEP 1] Installing RASA core...", 'blue')
    print_colored("[IMPORTANT] RASA installation typically takes 5-10 minutes!", 'yellow')
    print_colored("[INFO] Downloading and compiling 80+ dependencies including TensorFlow...", 'cyan')
    
    time_estimate, timeout_val = estimate_time("rasa==3.6.4")
    print_colored(f"[TIME] Estimated time: {time_estimate}", 'blue')
    
    rasa_success = install_package_individually("rasa==3.6.4", timeout_val, True)
    
    if rasa_success:
        print_colored("[SUCCESS] RASA core installed successfully!", 'green')
        time_estimate, timeout_val = estimate_time("rasa-sdk==3.6.1")
        print_colored(f"[TIME] Installing RASA SDK - Estimated time: {time_estimate}", 'blue')
        rasa_sdk_success = install_package_individually("rasa-sdk==3.6.1", timeout_val, False)
    else:
        print_colored("[ERROR] RASA core installation failed", 'red')
        print_colored("[INFO] Common causes:", 'yellow')
        print_colored("   - Slow internet connection", 'yellow')
        print_colored("   - Insufficient disk space", 'yellow')
        print_colored("   - Missing Visual Studio Build Tools (Windows)", 'yellow')
        print_colored("   - Conflicting dependencies", 'yellow')
        rasa_sdk_success = False
    
    # Read requirements and install one by one
    print_colored("[STEP 2] Installing dependencies ONE BY ONE...", 'blue')
    packages = read_requirements()
    
    # Remove RASA packages since we already installed them
    packages = [p for p in packages if not p.startswith('rasa==') and not p.startswith('rasa-sdk==')]
    
    print_colored(f"[INFO] Found {len(packages)} additional packages to install", 'blue')
    
    success_list = []
    failed_list = []
    
    if rasa_success:
        success_list.append("rasa==3.6.4")
    else:
        failed_list.append("rasa==3.6.4")
        
    if rasa_sdk_success:
        success_list.append("rasa-sdk==3.6.1")
    else:
        failed_list.append("rasa-sdk==3.6.1")
    
    # Install each package individually with time estimates
    for i, package in enumerate(packages, 1):
        time_estimate, timeout_val = estimate_time(package)
        print_colored(f"[PACKAGE] [{i}/{len(packages)}] Processing: {package}", 'blue')
        print_colored(f"[TIME] {time_estimate}", 'cyan')
        
        # Show live output for heavy packages
        show_live = any(heavy in package.lower() for heavy in ['tensorflow', 'torch', 'transformers', 'scipy'])
        
        if install_package_individually(package, timeout_val, show_live):
            success_list.append(package)
        else:
            failed_list.append(package)
        
        print()  # Add spacing
    
    # Summary Report
    print_colored("=" * 60, 'cyan')
    print_colored("[SUMMARY] INSTALLATION SUMMARY REPORT", 'cyan')
    print_colored("=" * 60, 'cyan')
    
    print_colored(f"[OK] SUCCESSFUL INSTALLATIONS ({len(success_list)}):", 'green')
    for package in success_list:
        print_colored(f"   + {package}", 'green')
    
    print()
    print_colored(f"[ERROR] FAILED INSTALLATIONS ({len(failed_list)}):", 'red')
    for package in failed_list:
        print_colored(f"   - {package}", 'red')
    
    # CRITICAL FIX: Force packaging version for RASA compatibility
    print()
    print_colored("[FIX] CRITICAL FIX: Enforcing RASA-compatible packaging version...", 'yellow')
    if run_command(".venv\\Scripts\\python.exe -m pip install packaging==20.9 --force-reinstall --no-deps", "Fixing packaging version for RASA"):
        print_colored("[OK] Packaging version fixed for RASA compatibility", 'green')
    else:
        print_colored("[WARN] Warning: Could not fix packaging version", 'yellow')
    
    print()
    print_colored("[TEST] Testing core installations...", 'blue')
    
    # Test installations
    test_results = {}
    test_packages = {
        "RASA": "import rasa; print('RASA:', rasa.__version__)",
        "RASA SDK": "import rasa_sdk; print('RASA SDK:', rasa_sdk.__version__)",
        "FastAPI": "import fastapi; print('FastAPI:', fastapi.__version__)",
        "Transformers": "import transformers; print('Transformers:', transformers.__version__)",
        "LangChain": "import langchain; print('LangChain:', langchain.__version__)",
        "FAISS": "import faiss; print('FAISS: Available')",
        "PyPDF": "import pypdf; print('PyPDF:', pypdf.__version__)"
    }
    
    for name, test_code in test_packages.items():
        if run_command(f".venv\\Scripts\\python.exe -c \"{test_code}\"", f"Testing {name}"):
            test_results[name] = "[OK] Working"
        else:
            test_results[name] = "[ERROR] Failed"
    
    print()
    print_colored("[RESULTS] COMPONENT TEST RESULTS:", 'blue')
    for name, result in test_results.items():
        color = 'green' if '[OK]' in result else 'red'
        print_colored(f"   {result} {name}", color)
    
    # Install frontend dependencies
    print()
    print_colored("[FRONTEND] Installing frontend dependencies...", 'blue')
    if run_command("npm --version", "Checking npm"):
        print_colored("[OK] npm available", 'green')
        
        # Install root dependencies
        if run_command("npm install", "Installing root package dependencies"):
            print_colored("[OK] Root dependencies installed", 'green')
        else:
            print_colored("[WARN] Root dependencies failed", 'yellow')
        
        # Install frontend dependencies
        if run_command("cd frontend && npm install", "Installing frontend dependencies"):
            print_colored("[OK] Frontend dependencies installed", 'green')
        else:
            print_colored("[WARN] Frontend dependencies failed", 'yellow')
    else:
        print_colored("[WARN] npm not found - frontend setup needed", 'yellow')
    
    print()
    print_colored("=" * 60, 'cyan')
    if len(failed_list) == 0:
        print_colored("[SUCCESS] ALL PACKAGES INSTALLED SUCCESSFULLY!", 'green')
        print_colored("[READY] Your RASA automotive chatbot is ready to go!", 'green')
    elif len(success_list) > len(failed_list):
        print_colored("[PARTIAL] MOSTLY SUCCESSFUL - Core functionality available!", 'yellow')
        if "rasa==3.6.4" in success_list:
            print_colored("[OK] RASA core is working - You can proceed with development!", 'green')
    else:
        print_colored("[WARN] MANY FAILURES - Check dependency conflicts", 'red')
        if "rasa==3.6.4" not in success_list:
            print_colored("[ERROR] RASA installation failed - This is critical for the project", 'red')
    print_colored("=" * 60, 'cyan')
    
    # Additional tips based on results
    if "rasa==3.6.4" not in success_list:
        print()
        print_colored("[HELP] RASA INSTALLATION TROUBLESHOOTING TIPS:", 'yellow')
        print_colored("1. Check internet connection speed", 'cyan')
        print_colored("2. Free up disk space (RASA needs ~2GB)", 'cyan')
        print_colored("3. On Windows: Install Visual Studio Build Tools", 'cyan')
        print_colored("4. Try running: pip install --upgrade setuptools wheel", 'cyan')
        print_colored("5. Consider using conda instead: conda install rasa", 'cyan')
    
    print_colored("[COMPLETE] Setup complete! Check the summary above for details.", 'cyan')

if __name__ == "__main__":
    main() 