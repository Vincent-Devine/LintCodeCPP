import re
from pathlib import Path
import sys

# -------------------
# CONFIG — Naming rules
# -------------------
CLASS_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')
FUNC_REGEX = re.compile(r'^[A-Z][A-Za-z0-9]*$')
MEMBER_NONSTATIC_REGEX = re.compile(r'^_[a-zA-Z0-9]+$')
MEMBER_STATIC_REGEX = re.compile(r'^s_[a-zA-Z0-9]+$')
GLOBAL_BAD_PREFIX_REGEX = re.compile(r'^_|^s_')

class_decl_regex = re.compile(r'\bclass\s+([A-Za-z_][A-Za-z0-9_]*)')
enum_decl_regex = re.compile(r'\benum\s+([A-Za-z_][A-Za-z0-9_]*)')
func_decl_regex = re.compile(r'\b[A-Za-z_][A-Za-z0-9_:<>]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(')
var_decl_regex = re.compile(r'^(?:\s*)(?:static\s+)?(?:const\s+)?(?:inline\s+)?[A-Za-z_][A-Za-z0-9_:<>\s,\*&]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;|\))')

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

# -------------------
# Get files from arguments
# -------------------
if len(sys.argv) < 2:
    print("No files to analyze.")
    sys.exit(0)

source_files = [Path(f) for f in sys.argv[1:] if Path(f).exists()]

# -------------------
# Collect symbols
# -------------------
project_classes = set()
project_functions = set()
project_member_vars_nonstatic = set()
project_member_vars_static = set()

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

        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name != "main": project_functions.add(name)

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

# -------------------
# Check naming + generate suggestions
# -------------------
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

        m = class_decl_regex.search(s)
        if m:
            name = m.group(1)
            if name in project_classes and not CLASS_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "function")

        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)
            if name != "main" and name in project_functions and not FUNC_REGEX.match(name):
                bad_name = name
                good_name = fix_name(name, "function")

        var = var_decl_regex.match(s)
        if var:
            name = var.group(1)
            if name in project_member_vars_static:
                if not MEMBER_STATIC_REGEX.match(name):
                    bad_name = name
                    good_name = fix_name(name, "static_member")
            elif name in project_member_vars_nonstatic:
                if not MEMBER_NONSTATIC_REGEX.match(name):
                    bad_name = name
                    good_name = fix_name(name, "member")
            elif GLOBAL_BAD_PREFIX_REGEX.match(name):
                bad_name = name
                good_name = name.lstrip("_s")

        if bad_name and good_name and bad_name != good_name:
            new_line = re.sub(r'\b' + re.escape(bad_name) + r'\b', good_name, original_line)
            suggestions_data.append(f"{file.as_posix()}|{idx}|{new_line}")
            print(f"::warning file={file},line={idx}::{bad_name} should be {good_name}")

if suggestions_data:
    with open("lint_suggestions.txt", "w", encoding="utf-8") as f:
        for item in suggestions_data:
            f.write(item + "\n")
    sys.exit(1)
