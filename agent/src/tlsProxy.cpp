
#include "tlsProxy.h"
#include "tokenGenerator.h"

#include <openssl/ssl.h>
#include <openssl/err.h>

#include <sys/socket.h>   
#include <netinet/in.h>   
#include <arpa/inet.h>    
#include <unistd.h>       

#include <cstring>   
#include <iostream>  
#include <thread>
#include <vector>

namespace rootduck {

namespace {

constexpr size_t BUFFER_SIZE = 16 * 1024;

int createListeningSocket(uint16_t port) {

    int listenFd = socket(AF_INET, SOCK_STREAM, 0);
    if (listenFd < 0) {
        std::cerr << "socket() failed\n";
        return -1;
    }

    int reuse = 1;
    setsockopt(listenFd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));

    sockaddr_in address{};                  
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;   
    address.sin_port = htons(port);         

    if (bind(listenFd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) < 0) {
        std::cerr << "bind() failed on port " << port << "\n";
        close(listenFd);
        return -1;
    }

    if (listen(listenFd, 16) < 0) {
        std::cerr << "listen() failed\n";
        close(listenFd);
        return -1;
    }

    return listenFd;
}

int connectToBackend(const std::string& host, uint16_t port) {
    int backendFd = socket(AF_INET, SOCK_STREAM, 0);
    if (backendFd < 0) {
        return -1;
    }

    sockaddr_in address{};
    address.sin_family = AF_INET;
    address.sin_port = htons(port);

    if (inet_pton(AF_INET, host.c_str(), &address.sin_addr) <= 0) {
        close(backendFd);
        return -1;
    }

    if (connect(backendFd, reinterpret_cast<sockaddr*>(&address), sizeof(address)) < 0) {
        close(backendFd);
        return -1;
    }

    return backendFd;
}

std::string readLineFromSsl(SSL* ssl, size_t maxLength = 512) {
    std::string line;
    char ch;
    while (line.size() < maxLength) {
        int bytesRead = SSL_read(ssl, &ch, 1);
        if (bytesRead <= 0) {
            break;  
        }
        if (ch == '\n') {
            break;
        }
        line.push_back(ch);
    }
    return line;
}

void relayLoop(SSL* ssl, int plainFd, bool fromSsl) {
    std::vector<char> buffer(BUFFER_SIZE);

    while (true) {
        int bytesRead;
        if (fromSsl) {
            bytesRead = SSL_read(ssl, buffer.data(), static_cast<int>(buffer.size()));
        } else {
            bytesRead = static_cast<int>(read(plainFd, buffer.data(), buffer.size()));
        }

        if (bytesRead <= 0) {
            break;  
        }

        if (fromSsl) {

            ssize_t written = write(plainFd, buffer.data(), bytesRead);
            if (written <= 0) break;
        } else {

            int written = SSL_write(ssl, buffer.data(), bytesRead);
            if (written <= 0) break;
        }
    }

    shutdown(plainFd, SHUT_RDWR);
}

void handleConnection(SSL_CTX* ctx, int clientFd, const TlsProxyConfig& config) {
    SSL* ssl = SSL_new(ctx);
    SSL_set_fd(ssl, clientFd);

    if (SSL_accept(ssl) <= 0) {
        ERR_print_errors_fp(stderr);
        SSL_free(ssl);
        close(clientFd);
        return;
    }

    std::string line = readLineFromSsl(ssl);
    const std::string prefix = "TOKEN: ";
    std::string candidateToken;
    if (line.rfind(prefix, 0) == 0) {  
        candidateToken = line.substr(prefix.size());
    }

    std::string storedHash = loadTokenHash(config.tokenHashPath);
    bool authorized = !storedHash.empty() && verifyToken(candidateToken, storedHash);

    if (!authorized) {
        const char* denied = "DENIED\n";
        SSL_write(ssl, denied, static_cast<int>(strlen(denied)));
        SSL_shutdown(ssl);
        SSL_free(ssl);
        close(clientFd);
        return;
    }

    const char* accepted = "OK: connection secured\n";
    SSL_write(ssl, accepted, static_cast<int>(strlen(accepted)));

    int backendFd = connectToBackend(config.backendHost, config.backendPort);
    if (backendFd < 0) {
        std::cerr << "Не удалось подключиться к backend "
                  << config.backendHost << ":" << config.backendPort << "\n";
        SSL_shutdown(ssl);
        SSL_free(ssl);
        close(clientFd);
        return;
    }

    std::thread backendToClient(relayLoop, ssl, backendFd, /*fromSsl=*/false);
    relayLoop(ssl, backendFd, /*fromSsl=*/true);  // клиент -> backend, в этом потоке

    backendToClient.join();  

    close(backendFd);
    SSL_shutdown(ssl);
    SSL_free(ssl);
    close(clientFd);
}

}  
void runTlsProxy(const TlsProxyConfig& config) {

    const SSL_METHOD* method = TLS_server_method();
    SSL_CTX* ctx = SSL_CTX_new(method);
    if (ctx == nullptr) {
        std::cerr << "SSL_CTX_new failed\n";
        return;
    }

    if (SSL_CTX_use_certificate_file(ctx, config.certPath.c_str(), SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
        SSL_CTX_free(ctx);
        return;
    }
    if (SSL_CTX_use_PrivateKey_file(ctx, config.keyPath.c_str(), SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
        SSL_CTX_free(ctx);
        return;
    }

    int listenFd = createListeningSocket(config.listenPort);
    if (listenFd < 0) {
        SSL_CTX_free(ctx);
        return;
    }

    std::cerr << "rootduck-agent: слушаю TLS-подключения на порту "
              << config.listenPort << "\n";

    while (true) {
        sockaddr_in clientAddr{};
        socklen_t clientAddrLen = sizeof(clientAddr);
        int clientFd = accept(listenFd, reinterpret_cast<sockaddr*>(&clientAddr), &clientAddrLen);
        if (clientFd < 0) {
            continue;  
        }

        std::thread(handleConnection, ctx, clientFd, config).detach();
    }

    close(listenFd);
    SSL_CTX_free(ctx);
}

}  