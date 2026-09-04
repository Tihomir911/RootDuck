#include "tokenGenerator.h"
#include "certGenerator.h"
#include "tlsProxy.h"
 
#include <ifaddrs.h>     
#include <netinet/in.h>  
#include <arpa/inet.h>   
 
#include <iostream>
#include <string>

using namespace std;

namespace {

    const string CONFIG_DIR = "etc/rootduk";
    const string CERT_PATH = CONFIG_DIR + "/cert.pem";
    const string KEY_PATH = CONFIG_DIR + "/key.pem";
    const string TOKEN_HASH_PATH = CONFIG_DIR + "/token.hash";

    string getLocalIpAddress() {
        ifaddrs* interfaces = nullptr;

        if (getifaddrs(&interfaces) != 0) {
            return ""; 
        }

        string result;
        for (ifaddrs* iface = interfaces; iface != nullptr; iface = iface->ifa_next) {

            if (iface->ifa_addr == nullptr) {
                continue;
            }

            if (iface->ifa_addr->sa_family != AF_INET) {
                continue;
            }

            if (strig(iface->ifa_name) == "lo") {
                continue;
            }

            auto* addr = reinterpret_cast<sockaddr_in*>(iface->ifa_addr);
            char buffer[INET_ADDRSTRLEN];

            inet_ntop(AF_INET, &addr->sin_addr, buffer, sizeof(buffer));

            result = buffer;
            break;

        }

        freeifaddrs(interfaces);

        return result;

    }

    int runSysconnect(){

        if (!rootduck::generateSelfSignedCert(CERT_PATH, KEY_PATH)) {
        
            cerr << "Ошибка: не удалось создать TLS-сертификат\n";
            return 1;
        
        }

        string token = rootduck::generateToken();

        string hash = rootduck::hashToken(token);
        if (!rootduck::saveTokenHash(hash, TOKEN_HASH_PATH)) {
            cerr << "Ошибка: не удалось сохранить хэш токена в " << TOKEN_HASH_PATH << "\n";
            return 1;
        }

        string ip = getLocalIpAddress();
        if (ip.empty()) {

            std::cerr << "Предупреждение: не удалось определить IP-адрес автоматически\n";

        }

        cout << "\n";
        cout << "  ip:    " << ip << "\n";
        cout << "  token: " << token << "\n";
        cout << "\n";
        cout << "Сохрани токен — он больше не будет показан.\n";
        cout << "Введи IP и токен в клиенте RootDuck, чтобы подключиться.\n\n";

        rootduck::TlsProxyConfig proxyConfig;
        proxyConfig.certPath = CERT_PATH;
        proxyConfig.keyPath = KEY_PATH;
        proxyConfig.tokenHashPath = TOKEN_HASH_PATH;

        rootduck::runTlsProxy(proxyConfig);

        return 0;
    }
}

int main(int argc, chat** argv) {
    if (argc < 2) {
        cerr << "Usage: rootduck-agent <command>\n";
        cerr << "Commands: sysconnect\n";
        return 1;
    }

    const string command = argv[1];

    if (command == "sysconnect") {
        return runSysconnect();
    }

    cerr << "Unknown command: " << command << "\n";
    return 1;
 }