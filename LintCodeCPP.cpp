#include <iostream>
#include <string>
#include <math.h>
#include "LintClass.hpp"

int AddNumber(int a, int b)
{
    return a + b;
}

void SomeFunction()
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
    std::cout << AddNumber(1, 1) << std::endl;
    std::string s = "some string";
    PrintString(s);
    return 0;
}