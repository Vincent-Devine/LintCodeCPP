import os
import re
import sys

# ----------------- CONFIGURATION -----------------
# Regex for valid snake_case function names (e.g., calculate_sum)
# It excludes 'main' which is often exempt.
SNAKE_CASE_REGEX = r'^(?!main\b)[a-z_][a-z0-9_]*$' 
# Regex to find potential function declarations/definitions
FUNCTION_DEF_PATTERN = re.compile(r'\b(?:void|int|float|double|bool|std::string|\w+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^;]*\)\s*(?:\{|;)')
# File extensions to check
EXTENSIONS = ('.cpp', '.h', '.hpp')
# -------------------------------------------------

def check_naming_conventions(file_path):
    """Checks a single C++ file for naming violations."""
    violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Search for function declarations/definitions
                match = FUNCTION_DEF_PATTERN.search(line)
                
                if match:
                    function_name = match.group(1)
                    # Check the extracted name against the snake_case rule
                    if not re.match(SNAKE_CASE_REGEX, function_name):
                        violations.append(
                            f"  -> Line {line_num}: Function '{function_name}' is not in snake_case."
                        )
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        
    return violations

def find_cpp_files(root_dir):
    """Finds all relevant C++ files in the repository."""
    cpp_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(EXTENSIONS):
                cpp_files.append(os.path.join(root, file))
    return cpp_files

if __name__ == "__main__":
    print("Starting Naming Convention Check...")
    
    all_violations = {}
    
    # 🚨 NOTE: For simplicity, this checks ALL files. 
    # For a large project, you'd limit this to only files changed by the PR/Push.
    files_to_check = find_cpp_files(os.getcwd())

    for file in files_to_check:
        violations = check_naming_conventions(file)
        if violations:
            all_violations[file] = violations

    if all_violations:
        print("\n--- 🛑 NAMING CONVENTION VIOLATIONS FOUND 🛑 ---")
        for file, violations in all_violations.items():
            print(f"\nFile: {file}")
            for violation in violations:
                print(violation)
                
        print(f"\nTotal files with violations: {len(all_violations)}")
        # 🚨 CRITICAL: Exit with a non-zero code to fail the GitHub Action
        sys.exit(1)
    else:
        print("\n--- ✅ All Naming Conventions Passed! ---")
        sys.exit(0)