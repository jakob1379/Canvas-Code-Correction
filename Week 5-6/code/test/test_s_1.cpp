#include "../SparseVector.hpp"
#include <iostream>
#include <array>
#include <algorithm>
#include "BasicTest.h"

template<class CI, class CV>
bool test_vector(SparseVector<double> const& vec, CI const& result_indices, CV const& result_values){
	if(vec.nonZeroes() != result_indices.size()){
		std::cout<<"not right number of NonZeroes"<<std::endl;
		return false;
	}
	
	//check indices
	for(std::size_t i = 0; i != result_indices.size(); ++i){
		if(vec.indexNonZero(i) != result_indices[i]){
			std::cout<<"indexNonZero; stored index not correct"<<std::endl;
			return false;
		}
	}
	
	//check values
	for(std::size_t i = 0; i != result_indices.size(); ++i){
		if(vec.valueNonZero(i) != result_values[i]){
			std::cout<<"stored value not correct"<<std::endl;
			return false;
		}
	}
	
	//check getValue for available numbers
	for(std::size_t i = 0; i != result_indices.size(); ++i){
		if(vec.getValue(result_indices[i]) != result_values[i]){
			std::cout<<"getValue not correct for existing index"<<std::endl;
			return false;
		}
	}
	
	for(std::size_t i = 0; i != vec.size(); ++i){
		if(std::find(result_indices.begin(),result_indices.end(),i) != result_indices.end())
			continue;//index exists
		if(vec.getValue(i) != 0.0){
			std::cout<<"getValue not correct for non-existing index"<<std::endl;
			return false;
		}
	}
	
	return true;
}


bool test();

int main() {
	BasicTest t1("sparse vector", "construct", "test_s_1.cpp.result.txt",test);
	t1.run();
	
	return 0;
}



bool test(){
	//Default ctor
    bool noError = true;
	{
		SparseVector<double> vec;
		if(vec.size() != 0 || vec.nonZeroes() != 0){
			std::cout<<"error in default constructor"<<std::endl;
            noError = false;
        }
	}
	
	//ctor with size
	{
		SparseVector<double> vec(5);
		if(vec.size() != 5 || vec.nonZeroes() != 0){
			std::cout<<"error in default constructor"<<std::endl;
            noError=false;
        }
	}
	
    return noError;
}


