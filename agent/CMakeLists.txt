cmake_minimum_required(VERSION 3.16)
project(rootduck-agent CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)

add_executable(rootduck-agent
    src/main.cpp
    src/tokenGenerator.cpp
    src/certGenerator.cpp
    src/tlsProxy.cpp
)

target_link_libraries(rootduck-agent PRIVATE
    OpenSSL::SSL
    OpenSSL::Crypto
    Threads::Threads
)