#pragma once 

#include <iostream>
#include <string>

using namespace std;

namecpace rootduck{

    string generateToken();

    string hashToken(const string& token);

    bool saveTokenHash(const string& hash, const string& filePath);

    string LoadTokenHash(const string& filePath);

    bool verifyToken(const string& candidateToken, const string& storedHash);
    
}