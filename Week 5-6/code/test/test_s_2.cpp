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
	BasicTest t1("sparse vector", "insertion, setValue, getValue etc", "test_s_2.cpp.result.txt",test);
	t1.run();
	
	return 0;
}

bool test(){
    bool noError = true;
	//insertion, setValue, getValue etc
	{
		std::array<unsigned int,8> indices = {3,8,12,8,5,14,3,11};
		std::array<double,8> values = {1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0};
		std::array<unsigned int,6> result_indices = {3,5,8,11,12,14};
		std::array<double,6> result_values = {7.0,5.0,4.0,8.0,3.0,6.0};
		
		SparseVector<double> vec1(200);
		for(std::size_t i = 0; i != result_indices.size(); ++i){
			vec1.setValue(result_indices[i], result_values[i]);
		}
		if(!test_vector(vec1,result_indices,result_values)){
			std::cout<<"insertion with ordered, unique indices failed"<<std::endl;
            noError = false;
		}
		
		SparseVector<double> vec2(200);
		for(std::size_t i = 0; i != indices.size(); ++i){
			vec2.setValue(indices[i], values[i]);
		}
		
		if(!test_vector(vec2,result_indices,result_values)){
			std::cout<<"insertion with unordered, duplicated indices failed"<<std::endl;
            noError = false;   
		}
		
	}
	
	return noError;
	
}
