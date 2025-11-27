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
# PASS 1 — Collect symbols that BELONG TO THE PROJECT
# (BUT IGNORE main)
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

        m = class_decl_regex.search(s)
        if m:
            project_classes.add(m.group(1))
            in_class = True
            continue

        if in_class and s.endswith('};'):
            in_class = False
            continue

        e = enum_decl_regex.search(s)
        if e:
            project_enums.add(e.group(1))

        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)

            # EXCEPTION FOR main :
            if name == "main":
                continue

            project_functions.add(name)

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
# PASS 2 — Check naming rules
# ============================================================

errors = []

def check(name, regex, msg):
    if not regex.match(name):
        errors.append(msg)


for file in source_files:
    text = file.read_text()
    lines = text.splitlines()

    for idx, line in enumerate(lines, 1):
        s = line.strip()

        # CLASS
        m = class_decl_regex.search(s)
        if m:
            name = m.group(1)
            if name in project_classes:
                check(name, CLASS_REGEX,
                      f"{file}:{idx} - Class '{name}' must be PascalCase")

        # FUNCTION
        f = func_decl_regex.search(s)
        if f:
            name = f.group(1)

            # EXCEPTION FOR main :
            if name == "main":
                continue

            if name in project_functions:
                check(name, FUNC_REGEX,
                      f"{file}:{idx} - Function '{name}' must be PascalCase")

        # ENUM
        e = enum_decl_regex.search(s)
        if e:
            name = e.group(1)
            if name in project_enums:
                check(name, ENUM_REGEX,
                      f"{file}:{idx} - Enum '{name}' must be PascalCase")

        # VARIABLES
        var = var_decl_regex.match(s)
        if var:
            name = var.group(1)
            is_static = "static" in s

            # Static member
            if name in project_member_vars_static:
                check(name, MEMBER_STATIC_REGEX,
                      f"{file}:{idx} - Static member '{name}' must be 's_varName'")
                continue

            # Non-static member
            if name in project_member_vars_nonstatic:
                check(name, MEMBER_NONSTATIC_REGEX,
                      f"{file}:{idx} - Member '{name}' must be '_varName'")
                continue

            # GLOBAL or LOCAL → must not start with "_" or "s_"
            if GLOBAL_BAD_PREFIX_REGEX.match(name):
                errors.append(
                    f"{file}:{idx} - Global/local variable '{name}' must NOT start with '_' or 's_'"
                )


# ============================================================
# OUTPUT
# ============================================================

# Après avoir collecté les erreurs dans la liste "errors"

with open("lint_output.txt", "w", encoding="utf-8") as f:
    if errors:
        for e in errors:
            f.write(e + "\n")
    else:
        f.write("NO_ERRORS")


if errors:
    print("❌ Naming errors detected:")
    for e in errors:
        print(" - " + e)
    sys.exit(1)

print("✔ All naming conventions are valid.")
