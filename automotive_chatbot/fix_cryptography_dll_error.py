#!/usr/bin/env python3
"""
🔧 CRYPTOGRAPHY DLL FIX FOR WINDOWS - RASA 3.6.4 COMPATIBILITY
Fixes: ImportError: DLL load failed while importing _rust: The specified procedure could not be found.

This error occurs when:
1. Incompatible cryptography version with Windows architecture
2. Missing Visual C++ redistributables  
3. Conflicting cryptography installations
4. Architecture mismatch (x86 vs x64)

SOLUTION: Install specific Windows-compatible cryptography version + dependencies
"""

import subprocess
import sys
import os
import platform
import time

def print_colored(message, color='white'):
    """Print colored messages - Windows safe"""
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

def run_command(command, description):
    """Run command and return success status"""
    try:
        print_colored(f"[FIX] {description}...", 'cyan')
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print_colored(f"[OK] {description} - SUCCESS", 'green')
            return True
        else:
            print_colored(f"[ERROR] {description} - FAILED", 'red')
            if result.stderr:
                print_colored(f"Error: {result.stderr}", 'red')
            return False
    except Exception as e:
        print_colored(f"[ERROR] {description} - ERROR: {str(e)}", 'red')
        return False

def check_system_info():
    """Display system information for debugging"""
    print_colored("[SYSTEM] SYSTEM INFORMATION:", 'blue')
    print_colored(f"   OS: {platform.system()} {platform.release()}", 'cyan')
    print_colored(f"   Architecture: {platform.architecture()[0]}", 'cyan')
    print_colored(f"   Python: {sys.version}", 'cyan')
    print_colored(f"   Platform: {platform.platform()}", 'cyan')
    print()

def fix_cryptography_dll():
    """Main fix function for cryptography DLL issues"""
    print_colored("=" * 70, 'cyan')
    print_colored("[FIX] CRYPTOGRAPHY DLL FIX FOR WINDOWS - RASA COMPATIBILITY", 'cyan')
    print_colored("=" * 70, 'cyan')
    
    check_system_info()
    
    # Check if we're in virtual environment
    if not os.path.exists('.venv'):
        print_colored("[ERROR] Virtual environment not found! Please create .venv first", 'red')
        return False
    
    python_exe = ".venv\\Scripts\\python.exe" if os.name == 'nt' else ".venv/bin/python"
    pip_exe = ".venv\\Scripts\\pip.exe" if os.name == 'nt' else ".venv/bin/pip"
    
    print_colored("[DIAG] DIAGNOSING CRYPTOGRAPHY ISSUE...", 'blue')
    
    # Step 1: Test current cryptography installation
    print_colored("Step 1: Testing current cryptography installation...", 'yellow')
    test_result = run_command(f'{python_exe} -c "import cryptography; print(f\'Cryptography version: {{cryptography.__version__}}\')"', 
                            "Testing cryptography import")
    
    if test_result:
        print_colored("[OK] Cryptography is working! The issue might be elsewhere.", 'green')
        # Test python-jose specifically
        jose_test = run_command(f'{python_exe} -c "from jose import jwt; print(\'python-jose working\')"', 
                              "Testing python-jose import")
        if jose_test:
            print_colored("[OK] python-jose is also working! Issue might be resolved.", 'green')
            return True
    
    print_colored("[FIX] APPLYING CRYPTOGRAPHY FIXES...", 'blue')
    
    # Step 2: Uninstall conflicting packages
    print_colored("Step 2: Removing conflicting cryptography packages...", 'yellow')
    packages_to_remove = [
        "cryptography",
        "python-jose",
        "PyJWT",
        "cffi",
        "pycparser"
    ]
    
    for package in packages_to_remove:
        run_command(f"{pip_exe} uninstall {package} -y", f"Removing {package}")
    
    # Step 3: Clear pip cache
    print_colored("Step 3: Clearing pip cache...", 'yellow')
    run_command(f"{pip_exe} cache purge", "Clearing pip cache")
    
    # Step 4: Upgrade essential build tools
    print_colored("Step 4: Upgrading build tools...", 'yellow')
    run_command(f"{pip_exe} install --upgrade pip setuptools wheel", "Upgrading build tools")
    
    # Step 5: Install Windows-compatible cryptography version
    print_colored("Step 5: Installing Windows-compatible cryptography...", 'yellow')
    
    # Try specific versions known to work on Windows
    cryptography_versions = [
        "cryptography==41.0.4",  # Known stable version
        "cryptography==40.0.2",  # Fallback version
        "cryptography==39.0.2"   # Older stable version
    ]
    
    cryptography_success = False
    for version in cryptography_versions:
        print_colored(f"🔄 Trying {version}...", 'cyan')
        if run_command(f"{pip_exe} install {version} --only-binary=cryptography --force-reinstall", 
                      f"Installing {version}"):
            # Test if this version works
            if run_command(f'{python_exe} -c "import cryptography; print(\'SUCCESS: cryptography imported\')"', 
                          "Testing cryptography import"):
                cryptography_success = True
                print_colored(f"✅ SUCCESS: {version} is working!", 'green')
                break
        print_colored(f"❌ {version} failed, trying next...", 'yellow')
    
    if not cryptography_success:
        print_colored("❌ All cryptography versions failed. Trying alternative approach...", 'red')
        
        # Alternative: Install pre-compiled wheel
        print_colored("🔄 Trying pre-compiled wheel installation...", 'cyan')
        run_command(f"{pip_exe} install --only-binary=all cryptography", "Installing pre-compiled cryptography")
    
    # Step 6: Install compatible cffi and pycparser
    print_colored("Step 6: Installing compatible supporting libraries...", 'yellow')
    run_command(f"{pip_exe} install cffi==1.15.1", "Installing cffi")
    run_command(f"{pip_exe} install pycparser==2.21", "Installing pycparser")
    
    # Step 7: Install python-jose WITHOUT cryptography extras first
    print_colored("Step 7: Installing python-jose (base version)...", 'yellow')
    if run_command(f"{pip_exe} install python-jose==3.3.0", "Installing python-jose base"):
        print_colored("✅ python-jose base installed successfully", 'green')
        
        # Now try to add cryptography support
        print_colored("🔄 Adding cryptography support to python-jose...", 'cyan')
        if not run_command(f"{pip_exe} install python-jose[cryptography]==3.3.0 --force-reinstall", 
                          "Installing python-jose with cryptography"):
            print_colored("⚠️ Cryptography extras failed, but base python-jose should work", 'yellow')
    
    # Step 8: Alternative JWT library as backup
    print_colored("Step 8: Installing alternative JWT library as backup...", 'yellow')
    run_command(f"{pip_exe} install PyJWT==2.8.0", "Installing PyJWT as backup")
    
    # Step 9: Final comprehensive test
    print_colored("🧪 FINAL TESTING...", 'blue')
    
    test_commands = [
        (f'{python_exe} -c "import cryptography; print(f\'✅ Cryptography {{cryptography.__version__}} - OK\')"', 
         "Testing cryptography"),
        (f'{python_exe} -c "from cryptography.hazmat.primitives.asymmetric import ec; print(\'✅ Cryptography EC - OK\')"', 
         "Testing cryptography.hazmat"),
        (f'{python_exe} -c "from cryptography.exceptions import UnsupportedAlgorithm; print(\'✅ Cryptography exceptions - OK\')"', 
         "Testing cryptography exceptions"),
        (f'{python_exe} -c "import jwt; print(f\'✅ JWT {{jwt.__version__}} - OK\')"', 
         "Testing JWT library"),
        (f'{python_exe} -c "from jose import jwt as jose_jwt; print(\'✅ python-jose - OK\')"', 
         "Testing python-jose"),
    ]
    
    success_count = 0
    for command, description in test_commands:
        if run_command(command, description):
            success_count += 1
    
    print_colored("=" * 70, 'cyan')
    print_colored("📊 FIX RESULTS:", 'cyan')
    print_colored("=" * 70, 'cyan')
    
    if success_count >= 3:
        print_colored("🎉 CRYPTOGRAPHY FIX SUCCESSFUL!", 'green')
        print_colored(f"✅ {success_count}/5 components are working", 'green')
        print_colored("🚀 You should now be able to run RASA training!", 'green')
        
        # Final RASA test
        print_colored("🧪 Testing RASA import...", 'blue')
        if run_command(f'{python_exe} -c "import rasa; print(\'✅ RASA import successful!\')"', 
                      "Testing RASA import"):
            print_colored("🎯 PERFECT! RASA is working with fixed cryptography!", 'green')
            return True
        else:
            print_colored("⚠️ RASA import still failing - may need RASA reinstallation", 'yellow')
            
    elif success_count >= 1:
        print_colored("🔧 PARTIAL SUCCESS - Some components fixed", 'yellow')
        print_colored(f"✅ {success_count}/5 components are working", 'yellow')
        print_colored("💡 Try running the teammate's RASA command again", 'cyan')
        
    else:
        print_colored("❌ FIX UNSUCCESSFUL", 'red')
        print_colored("🆘 ALTERNATIVE SOLUTIONS:", 'yellow')
        print_colored("1. Install Visual C++ Redistributable 2019-2022", 'cyan')
        print_colored("2. Use conda instead: conda install cryptography", 'cyan')
        print_colored("3. Try Python 3.9.13 specifically", 'cyan')
        print_colored("4. Check Windows architecture (x64 vs x86)", 'cyan')
    
    print_colored("=" * 70, 'cyan')
    return success_count >= 3

def show_additional_tips():
    """Show additional troubleshooting tips"""
    print_colored("\n🔍 ADDITIONAL TROUBLESHOOTING TIPS:", 'blue')
    print_colored("=" * 50, 'blue')
    
    tips = [
        "1. Ensure Visual C++ Redistributable 2019-2022 is installed",
        "2. Try running as Administrator if permission issues occur",
        "3. Check Windows architecture matches Python (both 64-bit or both 32-bit)",
        "4. Clear all Python cache: python -c 'import sys; print(sys.path)'",
        "5. If still failing, try conda: conda install cryptography python-jose",
        "6. Alternative: Use Docker for consistent environment",
        "7. Check antivirus software isn't blocking DLL loading",
        "8. Verify internet connection for downloading binary wheels"
    ]
    
    for tip in tips:
        print_colored(f"   {tip}", 'cyan')
    
    print_colored("\n📧 If issues persist, the fix file will remain for debugging", 'yellow')

if __name__ == "__main__":
    print_colored("🚀 Starting cryptography DLL fix...", 'blue')
    success = fix_cryptography_dll()
    show_additional_tips()
    
    if success:
        print_colored("\n🎉 Fix completed successfully! Try running RASA again.", 'green')
        exit(0)
    else:
        print_colored("\n⚠️ Fix partially successful. Check tips above.", 'yellow')
        exit(1) 