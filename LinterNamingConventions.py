import re
from pathlib import Path
import sys

# ============================================================
# CONFIG — Naming rules
# ============================================================

CLASS_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')           # PascalCase
FUNC_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')            # PascalCase
MEMBER_NONSTATIC_REGEX = re.compile(r'^_[a-zA-Z0-9]+$')    # _camelCase
MEMBER_STATIC_REGEX = re.compile(r'^s_[a-zA-Z0-9]+$')      # s_var
ENUM_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')
GLOBAL_BAD_PREFIX_REGEX = re.compile(r'^_|^s_')            # forbidden for globals


# ============================================================
# REGEX extractors
# ============================================================
class_decl_regex = re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)')
enum_decl_regex = re.compile(r'\benum\s+([A-Za-z_][A-Za-z0-9_]*)')
func_decl_regex = re.compile(
    r'\b[A-Za-z_][A-Za-z0-9_:<>]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\('
)
var_decl_regex = re.compile(
    r'^(?:static\s+)?(?:const\s+)?[A-Za-z_][A-Za-z0-9_:<>\s,\*&]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;|\))'
)

# ============================================================
# FIX NAME FUNCTION
# ============================================================
def fix_name(name, kind):
    """
    Retourne le nom corrigé automatiquement
    kind = 'member', 'static_member', 'function'
    """
    if kind == "member":
        if not name.startswith("_"):
            return "_" + name
    elif kind == "static_member":
        if name.startswith("_"):
            return "s_" + name[1:]
        elif not name.startswith("s_"):
            return "s_" + name
    elif kind == "function":
        # Transform snake_case to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts if p)
    return name


# ============================================================
# PASS 1 — Collect project symbols
# ============================================================

project_classes = set()
project_functions = set()
project_member_vars_nonstatic = set()
project_member_vars_static = set()
project_enums = set()

source_files = list(Path('.').rglob('*.h')) + \
               list(Path('.').rglob('*.hpp')) + \
               list(Path('.').rglob('*.cpp'))

for file in source_files:
    text = file.read_text()
    lines = text.splitlines()

    in_class = False

    for line in lines:
        s = line.strip()

        # Class
        m = class_decl_regex.search(s)
        if m:
            project_classes.add(m.group(1))
            in_class = True
            continue

        if in_class and s.endswith('};'):
            in_class = False
            continue

        # Enum
        e = enum_decl_regex.search(s)
        if e:
            project_enums.add(e.group(1))

        # Function
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name == "main":  # exception
                continue
            project_functions.add(name)

        # Variable inside class
        if in_class:
            is_static = "static" in s
            mvar = var_decl_regex.match(s)
            if mvar:
                name = mvar.group(1)
                if is_static:
                    project_member_vars_static.add(name)
                else:
                    project_member_vars_nonstatic.add(name)

# ============================================================
# PASS 2 — Check naming + generate suggestions
# ============================================================

errors = []
suggestions = []

for file in source_files:
    text = file.read_text()
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        s = line.strip()

        # CLASS
        m = class_decl_regex.search(s)
        if m:
            name = m.group(1)
            if name in project_classes and not CLASS_REGEX.match(name):
                corrected = fix_name(name, "function")
                msg = f"{file}:{idx} - Class '{name}' must be PascalCase → suggested: '{corrected}'"
                errors.append(msg)
                suggestions.append(msg)
                print(msg)

        # FUNCTION
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name == "main":
                continue
            if name in project_functions and not FUNC_REGEX.match(name):
                corrected = fix_name(name, "function")
                msg = f"{file}:{idx} - Function '{name}' must be PascalCase → suggested: '{corrected}'"
                errors.append(msg)
                suggestions.append(msg)
                print(msg)
        
        # ENUM
        e = enum_decl_regex.search(s)
        if e:
            name = e.group(1)
            if name in project_enums and not ENUM_REGEX.match(name):
                msg = f"{file}:{idx} - Enum '{name}' must be PascalCase"
                errors.append(msg)
                suggestions.append(msg)
                print(msg)

        # VARIABLES
        var = var_decl_regex.match(s)
        if var:
            name = var.group(1)
            is_static = "static" in s

            if name in project_member_vars_static:
                if not MEMBER_STATIC_REGEX.match(name):
                    corrected = fix_name(name, "static_member")
                    msg = f"{file}:{idx} - Static member '{name}' must be 's_varName' → suggested: '{corrected}'"
                    errors.append(msg)
                    suggestions.append(msg)
                    print(msg)
                continue

            if name in project_member_vars_nonstatic:
                if not MEMBER_NONSTATIC_REGEX.match(name):
                    corrected = fix_name(name, "member")
                    msg = f"{file}:{idx} - Member '{name}' must be '_varName' → suggested: '{corrected}'"
                    errors.append(msg)
                    suggestions.append(msg)
                    print(msg)
                continue

            # GLOBAL / LOCAL → no _ or s_ allowed
            if GLOBAL_BAD_PREFIX_REGEX.match(name):
                corrected = name.lstrip("_s")
                msg = f"{file}:{idx} - Global/local variable '{name}' must NOT start with '_' or 's_' → suggested: '{corrected}'"
                errors.append(msg)
                suggestions.append(msg)
                print(msg)

# ============================================================
# OUTPUT FILE
# ============================================================

with open("lint_suggestions.txt", "w", encoding="utf-8") as f:
    if errors:
        for e in errors:
            f.write(e + "\n")
        f.write("\n### Suggested corrections:\n")
        for s in suggestions:
            f.write(s + "\n")
    else:
        f.write("NO_ERRORS\n")

# EXIT CODE
if errors:
    sys.exit(1)

print("✔ All naming conventions are valid.")
