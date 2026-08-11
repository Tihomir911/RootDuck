#pragma once

#include <string>

namespace rootduck {
 
bool generateSelfSignedCert(const std::string& certPath,
                             const std::string& keyPath,
                             int validityDays = 3650);
 
}