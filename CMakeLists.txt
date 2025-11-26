cmake_minimum_required(VERSION 3.10)
project(LinterHelper)

# Automatically find all source files
file(GLOB_RECURSE SOURCES 
    "*.cpp" 
    "*.h" 
    "src/*.cpp"      # Adjust these paths to match your folders
    "include/*.h"
)

add_executable(dummy_target ${SOURCES})

# IMPORTANT: List your include directories here!
# If clang-tidy complains it "cannot find header.h", add the folder here.
target_include_directories(dummy_target PUBLIC 
    "src"
    "include"
    # "C:/Program Files (x86)/SomeLib/include"  <-- You can even add system paths if needed
)