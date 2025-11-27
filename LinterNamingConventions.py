import re
from pathlib import Path
import sys

# ============================================================
# CONFIG — Naming rules
# ============================================================

CLASS_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')           # PascalCase
FUNC_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')             # PascalCase
MEMBER_NONSTATIC_REGEX = re.compile(r'^_[a-zA-Z0-9]+$')     # _camelCase
MEMBER_STATIC_REGEX = re.compile(r'^s_[a-zA-Z0-9]+$')       # s_var
ENUM_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')
GLOBAL_BAD_PREFIX_REGEX = re.compile(r'^_|^s_')            # forbidden for globals/locals

# ============================================================
# REGEX extractors
# ============================================================
class_decl_regex = re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)')
enum_decl_regex = re.compile(r'\benum\s+([A-Za-z_][A-Za-z0-9_]*)')
func_decl_regex = re.compile(r'\b[A-Za-z_][A-Za-z0-9_:<>]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(')
var_decl_regex = re.compile(r'^(?:\s*)(?:static\s+)?(?:const\s+)?(?:inline\s+)?[A-Za-z_][A-Za-z0-9_:<>\s,\*&]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;|\))')

# ============================================================
# FIX NAME FUNCTION
# ============================================================
def fix_name(name, kind):
    if kind == "member":
        if not name.startswith("_"): return "_" + name
    elif kind == "static_member":
        if name.startswith("_"): return "s_" + name[1:]
        elif not name.startswith("s_"): return "s_" + name
    elif kind == "function":
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
    try:
        text = file.read_text(encoding='utf-8')
    except:
        continue
        
    lines = text.splitlines()
    in_class = False

    for line in lines:
        s = line.strip()

        # Class detection
        m = class_decl_regex.search(s)
        if m:
            project_classes.add(m.group(1))
            in_class = True
            continue

        if in_class and s.endswith('};'):
            in_class = False
            continue

        # Enum detection
        e = enum_decl_regex.search(s)
        if e: project_enums.add(e.group(1))

        # Function detection
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name != "main": project_functions.add(name)

        # Member variable detection
        if in_class:
            mvar = var_decl_regex.match(s)
            if mvar:
                name = mvar.group(1)
                if '(' in s or ')' in s: continue 
                
                is_static = "static" in s
                if is_static:
                    project_member_vars_static.add(name)
                else:
                    project_member_vars_nonstatic.add(name)

# ============================================================
# PASS 2 — Check naming + generate suggestions
# ============================================================

suggestions_data = []

for file in source_files:
    try:
        text = file.read_text(encoding='utf-8')
    except:
        continue
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        s = line.strip()
        original_line = line
        
        bad_name = None
        good_name = None
        
        # 1. CLASS CHECK
        m = class_decl_regex.search(s)
        if m:
            name = m.group(1)
            if name in project_classes and not CLASS_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "function") # PascalCase

        # 2. FUNCTION CHECK
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name != "main" and name in project_functions and not FUNC_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "function")

        # 3. VARIABLE CHECK
        var = var_decl_regex.match(s)
        if var:
            name = var.group(1)
            
            # Case A: Known Static Member
            if name in project_member_vars_static:
                if not MEMBER_STATIC_REGEX.match(name):
                    bad_name = name
                    good_name = fix_name(name, "static_member")

            # Case B: Known Non-Static Member
            elif name in project_member_vars_nonstatic:
                if not MEMBER_NONSTATIC_REGEX.match(name):
                    bad_name = name
                    good_name = fix_name(name, "member")

            # Case C: Global or Local Variable (Not in member sets)
            elif GLOBAL_BAD_PREFIX_REGEX.match(name):
                 bad_name = name
                 good_name = name.lstrip("_s")
            
        # GENERATE OUTPUT
        if bad_name and good_name and bad_name != good_name:
            new_line = re.sub(r'\b' + re.escape(bad_name) + r'\b', good_name, original_line)
            suggestions_data.append(f"{file}|{idx}|{new_line}")
            print(f"::warning file={file},line={idx}::{bad_name} should be {good_name}")

if suggestions_data:
    with open("lint_suggestions.txt", "w", encoding="utf-8") as f:
        for item in suggestions_data:
            f.write(item + "\n")
    sys.exit(1)