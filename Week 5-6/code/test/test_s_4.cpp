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
	BasicTest t1("sparse vector", "assignment operator", "test_s_4.cpp.result.txt",test);
	t1.run();
	
	return 0;
}

bool test(){
    bool noError = true;
    //assignment operator
	{
		std::array<unsigned int,6> indices1 = {3,5,8,11,12,14};
		std::array<unsigned int,4> indices2 = {1,2,3,4};
		std::array<double,6> values1 = {7.0,5.0,4.0,8.0,3.0,6.0};
		std::array<double,4> values2 = {3.0,2.0,1.0,0.0};
		
		SparseVector<double> vec1(200);
		for(std::size_t i = 0; i != indices1.size(); ++i){
			vec1.setValue(indices1[i], values1[i]);
		}
		SparseVector<double> vec2(100);
		for(std::size_t i = 0; i != indices2.size(); ++i){
			vec2.setValue(indices2[i], values2[i]);
		}
		
		vec2=vec1;
		if(!test_vector(vec2,indices1,values1)){
			std::cout<<"operator= failed"<<std::endl;
            noError = false;
		}
	}
	return noError;
	
}
