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
	BasicTest t1("sparse vector", "math operators", "test_s_5.cpp.result.txt",test);
	t1.run();
	
	return 0;
}

bool test(){
    bool noError = true;
    //assignment operator
//math operators
	{
		std::array<unsigned int,6> indices1 = {3,5,8,11,12,14};
		std::array<double,6> values1 = {7.0,5.0,4.0,8.0,3.0,6.0};
		std::array<unsigned int,6> indices2 = {3,6,8,10,12,13};
		std::array<double,6> values2 = {7.0,5.0,4.0,8.0,3.0,6.0};
		
		std::array<unsigned int,9> result_indices = {3,5,6,8,10,11,12,13,14};
		std::array<double,9> result_values_add = {14.0,5.0,5.0,8.0, 8.0, 8.0,6.0,6.0,6.0};
		std::array<double,9> result_values_subtract = {0,5.0,-5,0,-8.0,8.0,0.0,-6.0,6.0};
		std::array<double,6> result_values_add_same = {14.0,10.0,8.0,16.0,6.0,12.0};
		std::array<double,6> result_values_subtract_same = {0,0,0,0,0,0};
		
		SparseVector<double> vec1(200);
		for(std::size_t i = 0; i != indices1.size(); ++i){
			vec1.setValue(indices1[i], values1[i]);
		}
		SparseVector<double> vec2(200);
		for(std::size_t i = 0; i != indices2.size(); ++i){
			vec2.setValue(indices2[i], values2[i]);
		}
		
		//operator+=
		{
			SparseVector<double> vec3 = vec1;
			vec3 += vec1;
			if(!test_vector(vec3,indices1,result_values_add_same)){
				std::cout<<"SparseVector<double> x=y; x+=y failed"<<std::endl;
                noError = false;
			}
		}
		{
			SparseVector<double> vec3 = vec1;
			vec3+= vec2;//this might crash for unsafe implementations
			if(!test_vector(vec3,result_indices,result_values_add)){
				std::cout<<"SparseVector<double> x=y; x+=z failed"<<std::endl;
                noError = false;
			}
		}
		{
			SparseVector<double> vec3 = vec1;
			vec3+= vec3;//this might crash for unsafe implementations
			if(!test_vector(vec3,indices1,result_values_add_same)){
				std::cout<<"SparseVector<double> x=y; x+=x failed"<<std::endl;
                noError = false;
			}
		}
		//operator+
		{
			SparseVector<double> vec3 = vec1+vec2;
			if(!test_vector(vec3,result_indices,result_values_add)){
				std::cout<<"SparseVector<double> x= y+z failed"<<std::endl;
                noError = false;
			}
		}
		
		//operator-=
		{
			SparseVector<double> vec3 = vec1;
			vec3 -= vec1;
			if(!test_vector(vec3,indices1,result_values_subtract_same)){
				std::cout<<"SparseVector<double> x=y; x-=y failed"<<std::endl;
                noError = false;
			}
		}
		{
			SparseVector<double> vec3 = vec1;
			vec3-= vec2;//this might crash for unsafe implementations
			if(!test_vector(vec3,result_indices,result_values_subtract)){
				std::cout<<"SparseVector<double> x=y; x-=z failed"<<std::endl;
                noError = false;
			}
		}
		{
			SparseVector<double> vec3 = vec1;
			vec3-= vec3;//this might crash for unsafe implementations
			if(!test_vector(vec3,indices1,result_values_subtract_same)){
				std::cout<<"SparseVector<double> x=y; x-=x failed"<<std::endl;
                noError = false;
			}
		}
		//operator+
		{
			SparseVector<double> vec3 = vec1-vec2;
			if(!test_vector(vec3,result_indices,result_values_subtract)){
				std::cout<<"SparseVector<double> x= y-z failed"<<std::endl;
                noError = false;
			}
		}
		
		
	}
	return noError;
	
}
