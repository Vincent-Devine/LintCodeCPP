#pragma once
class LintClass
{
private:
	int _bigNumber;
	int _NoneNumber;
	int number;
	static int s_staticGood;
	static int _staticBad1;
	static int staticBad2;

public:
	LintClass();
	bool Initialiation();
	void update();
	void windows_should_close();
};

