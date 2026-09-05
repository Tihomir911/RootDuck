#include "tokenGenerator.h"

#include <openssl/rand.h>
#include <openssl/sha.h>
#include <openssl/crypto.h>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <iomanip>

namespace rootduck {

    namespace {
        std::string bytesToHex(const unsigned char* data, size_t length) {
        std::ostringstream oss;
        for (size_t i = 0; i < length; ++i) {
        
            oss << std::hex << std::setw(2) << std::setfill('0')
                << static_cast<int>(data[i]);
        }
        return oss.str();
        }
    }  

    std::string generateToken() {
        constexpr size_t TOKEN_BYTES = 32; 
        unsigned char buffer[TOKEN_BYTES];

        if (RAND_bytes(buffer, TOKEN_BYTES) != 1) {
        
            throw std::runtime_error("RAND_bytes failed");
        }

        return bytesToHex(buffer, TOKEN_BYTES); 
    }

    std::string hashToken(const std::string& token) {
        unsigned char digest[SHA256_DIGEST_LENGTH];

        SHA256(reinterpret_cast<const unsigned char*>(token.data()),
            token.size(),
            digest);

        return bytesToHex(digest, SHA256_DIGEST_LENGTH); 
    }

    bool saveTokenHash(const std::string& hash, const std::string& filePath) {
        try {
            std::filesystem::path path(filePath);

            if (!path.parent_path().empty()) {
                std::filesystem::create_directories(path.parent_path());
            }

            std::ofstream out(filePath, std::ios::trunc);
            if (!out.is_open()) {
                return false; 
            }
            out << hash;
            out.close();

            std::filesystem::permissions(
                path,
                std::filesystem::perms::owner_read | std::filesystem::perms::owner_write,
                std::filesystem::perm_options::replace);

            return true;
        } catch (const std::exception&) {
        
            return false;
        }
    }

    std::string loadTokenHash(const std::string& filePath) {
        std::ifstream in(filePath);
        if (!in.is_open()) {
            return "";  
        }

        std::ostringstream buffer;
        buffer << in.rdbuf();  
        return buffer.str();
    }

    bool verifyToken(const std::string& candidateToken, const std::string& storedHash) {
    
    std::string candidateHash = hashToken(candidateToken);

        if (candidateHash.size() != storedHash.size()) {
            return false;
        }

        int result = CRYPTO_memcmp(candidateHash.data(), storedHash.data(), candidateHash.size());

        return result == 0;  
    }

}  