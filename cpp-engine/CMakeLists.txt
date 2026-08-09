cmake_minimum_required(VERSION 3.14)
project(medflow_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(pybind11 REQUIRED)
include_directories(include)

file(GLOB SOURCES "src/*.cpp")
pybind11_add_module(medflow_engine ${SOURCES})
