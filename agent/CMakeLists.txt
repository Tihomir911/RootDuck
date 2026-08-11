cmake_minimum_required(VERSION 3.16)
project(rootduck-agent CXX)
 
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenSSL REQUIRED)

add_executable(rootduck-agent
    src/main.cpp
    src/tokenGenerator.cpp
)

target_link_libraries(rootduck-agent PRIVATE OpenSSL::SSL OpenSSL::Crypto)