#pragma once

#include <string>

namespace rootduck {

std::string generateToken();

std::string hashToken(const std::string& token);

bool saveTokenHash(const std::string& hash, const std::string& filePath);

std::string loadTokenHash(const std::string& filePath);

bool verifyToken(const std::string& candidateToken, const std::string& storedHash);

}  