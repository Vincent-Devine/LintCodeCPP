import re
from pathlib import Path
import sys

# ... (Configuration and Regex definitions remain the same as your code) ...
# ... (Use your existing definitions for regex here) ...

# RE-INSERTING YOUR CONFIG FOR COMPLETENESS
CLASS_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')           # PascalCase
FUNC_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')             # PascalCase
MEMBER_NONSTATIC_REGEX = re.compile(r'^_[a-zA-Z0-9]+$')     # _camelCase
MEMBER_STATIC_REGEX = re.compile(r'^s_[a-zA-Z0-9]+$')       # s_var
ENUM_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')
GLOBAL_BAD_PREFIX_REGEX = re.compile(r'^_|^s_')

class_decl_regex = re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)')
enum_decl_regex = re.compile(r'\benum\s+([A-Za-z_][A-Za-z0-9_]*)')
func_decl_regex = re.compile(r'\b[A-Za-z_][A-Za-z0-9_:<>]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(')
var_decl_regex = re.compile(r'^(?:static\s+)?(?:const\s+)?[A-Za-z_][A-Za-z0-9_:<>\s,\*&]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;|\))')

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
# LOGIC
# ============================================================

project_classes = set()
project_functions = set()
project_member_vars_nonstatic = set()
project_member_vars_static = set()
project_enums = set()

source_files = list(Path('.').rglob('*.h')) + list(Path('.').rglob('*.hpp')) + list(Path('.').rglob('*.cpp'))

# --- PASS 1: Collect Symbols (No changes needed) ---
for file in source_files:
    try:
        text = file.read_text(encoding='utf-8')
    except:
        continue 
    lines = text.splitlines()
    in_class = False
    for line in lines:
        s = line.strip()
        m = class_decl_regex.search(s)
        if m:
            project_classes.add(m.group(1))
            in_class = True
            continue
        if in_class and s.endswith('};'):
            in_class = False
            continue
        e = enum_decl_regex.search(s)
        if e: project_enums.add(e.group(1))
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name != "main": project_functions.add(name)
        if in_class:
            is_static = "static" in s
            mvar = var_decl_regex.match(s)
            if mvar:
                name = mvar.group(1)
                if is_static: project_member_vars_static.add(name)
                else: project_member_vars_nonstatic.add(name)

# --- PASS 2: Check & Generate Full Line Replacement ---
suggestions_data = []

for file in source_files:
    try:
        text = file.read_text(encoding='utf-8')
    except:
        continue
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        s = line.strip() # Used for matching
        original_line = line # Used for replacement (preserves indentation)
        
        bad_name = None
        good_name = None
        
        # 1. Check Classes
        m = class_decl_regex.search(s)
        if m:
            name = m.group(1)
            if name in project_classes and not CLASS_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "function")

        # 2. Check Functions
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name != "main" and name in project_functions and not FUNC_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "function")

        # 3. Check Enums
        e = enum_decl_regex.search(s)
        if e:
            name = e.group(1)
            if name in project_enums and not ENUM_REGEX.match(name):
                 # No fix logic for Enum in your script, skipping replacement logic
                 pass

        # 4. Check Variables
        var = var_decl_regex.match(s)
        if var:
            name = var.group(1)
            if name in project_member_vars_static and not MEMBER_STATIC_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "static_member")
            elif name in project_member_vars_nonstatic and not MEMBER_NONSTATIC_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "member")
            elif GLOBAL_BAD_PREFIX_REGEX.match(name):
                bad_name = name
                good_name = name.lstrip("_s")

        # GENERATE OUTPUT IF ERROR FOUND
        if bad_name and good_name:
            # Smart replace: only replace the whole word \bNAME\b
            # This prevents replacing 'var' inside 'variable'
            new_line = re.sub(r'\b' + re.escape(bad_name) + r'\b', good_name, original_line)
            
            # FORMAT: File|Line|New_Code_Content
            # We use a custom separator | to make parsing in JS easy
            suggestions_data.append(f"{file}|{idx}|{new_line}")
            print(f"::warning file={file},line={idx}::{bad_name} should be {good_name}")

# WRITE TO FILE
if suggestions_data:
    with open("lint_suggestions.txt", "w", encoding="utf-8") as f:
        for item in suggestions_data:
            f.write(item + "\n")
    sys.exit(1)