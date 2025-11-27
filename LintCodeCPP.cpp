#include <iostream>
#include <string>
#include <math.h>
#include "LintClass.hpp"

int AddNumber(int a, int b)
{
    return a + b;
}

void some_function()
{
    std::cout << "some function" << std::endl;
}

void PrintString(std::string s)
{
    std::cout << s << std::endl;
}

int main()
{
    std::cout << "Hello World!" << std::endl;
    std::cout << std::to_string(2);
    std::cout << " = " << AddNumber(1, 1) << std::endl;
    std::string s = "some string";
    PrintString(s);
    return 0;
}