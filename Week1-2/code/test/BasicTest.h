/*
 * BasicTest.h
 *
 *  Created on: Apr 3, 2015
 *      Author: casper
 */

#ifndef TEST_BASICTEST_H_
#define TEST_BASICTEST_H_

#include <string>

bool compareDouble(double a, double b, double eps);

class BasicTest {
	public:
		BasicTest(std::string n, std::string d, std::string path, bool (*f)());
		//~BasicTest();
		void run();
	private:
		std::string name;
		std::string description;		
		std::string pathToResultFile;
		virtual std::string evaluate();
		bool (*testFunction)();
	

};


#endif /* TEST_BASICTEST_H_ */
