#pragma once
 
#include <cstdint>
#include <string>
 
namespace rootduck {
 
    struct TlsProxyConfig {
        std::string certPath;
        std::string keyPath;
        std::string tokenHashPath;
        uint16_t listenPort = 9443;
        std::string backendHost = "127.0.0.1";
        uint16_t backendPort = 8000;
    };
 
 void runTlsProxy(const TlsProxyConfig& config);
 
} 