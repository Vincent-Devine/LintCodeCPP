#include <iostream>
#include <string>

int AddNumber(int a, int b)
{
    return a + b;
}

void SomeFunction()
{
    std::cout << "some function" << std::endl;
}

int main()
{
    std::cout << "Hello World!" << std::endl;
    std::cout << AddNumber(1, 1) << std::endl;
    return 0;
}