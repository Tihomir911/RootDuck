#include "certGenerator.h"
 
#include <openssl/evp.h>   // EVP_PKEY, EVP_RSA_gen — генерация ключа
#include <openssl/x509.h>  // X509, X509_NAME — работа с сертификатом
#include <openssl/pem.h>   // PEM_write_PrivateKey, PEM_write_X509 — сохранение в файлы
 
#include <filesystem>
#include <memory>     // std::unique_ptr — для RAII-обёрток над EVP_PKEY/X509
#include <stdexcept>
 
namespace rootduck {
 
namespace {

using EvpKeyPtr = std::unique_ptr<EVP_PKEY, decltype(&EVP_PKEY_free)>;
using X509Ptr = std::unique_ptr<X509, decltype(&X509_free)>;
 
EvpKeyPtr generateRsaKey() {
    
    EVP_PKEY* rawKey = EVP_RSA_gen(2048);
    if (rawKey == nullptr) {
        throw std::runtime_error("EVP_RSA_gen failed: не удалось сгенерировать RSA-ключ");
    }
    
    return EvpKeyPtr(rawKey, EVP_PKEY_free);
}

X509Ptr buildSelfSignedX509(EVP_PKEY* key, int validityDays) {
    X509Ptr cert(X509_new(), X509_free);
    if (!cert) {
        throw std::runtime_error("X509_new failed");
    }

    X509_set_version(cert.get(), 2);

    ASN1_INTEGER_set(X509_get_serialNumber(cert.get()), 1);
 
    X509_gmtime_adj(X509_getm_notBefore(cert.get()), 0);
    X509_gmtime_adj(X509_getm_notAfter(cert.get()), static_cast<long>(validityDays) * 86400L);
 
    X509_set_pubkey(cert.get(), key);
 
   
    X509_NAME* name = X509_get_subject_name(cert.get());
    X509_NAME_add_entry_by_txt(
        name, "CN", MBSTRING_ASC,
        reinterpret_cast<const unsigned char*>("rootduck"), -1, -1, 0);
 
    
    X509_set_issuer_name(cert.get(), name);
 
    
    if (X509_sign(cert.get(), key, EVP_sha256()) == 0) {
        throw std::runtime_error("X509_sign failed: не удалось подписать сертификат");
    }
 
    return cert;
}
 
void writeKeyToFile(EVP_PKEY* key, const std::string& path) {
    FILE* file = fopen(path.c_str(), "wb");
    if (file == nullptr) {
        throw std::runtime_error("Не удалось открыть файл для записи ключа: " + path);
    }
    
    int result = PEM_write_PrivateKey(file, key, nullptr, nullptr, 0, nullptr, nullptr);
    fclose(file);
    if (result == 0) {
        throw std::runtime_error("PEM_write_PrivateKey failed");
    }
}
 
void writeCertToFile(X509* cert, const std::string& path) {
    FILE* file = fopen(path.c_str(), "wb");
    if (file == nullptr) {
        throw std::runtime_error("Не удалось открыть файл для записи сертификата: " + path);
    }
    int result = PEM_write_X509(file, cert);
    fclose(file);
    if (result == 0) {
        throw std::runtime_error("PEM_write_X509 failed");
    }
}
 
}  

bool generateSelfSignedCert(const std::string& certPath,
                             const std::string& keyPath,
                             int validityDays) {
    try {

        if (std::filesystem::exists(certPath) && std::filesystem::exists(keyPath)) {
            return true;
        }
 
        std::filesystem::path certFsPath(certPath);
        if (!certFsPath.parent_path().empty()) {
            std::filesystem::create_directories(certFsPath.parent_path());
        }
 
        EvpKeyPtr key = generateRsaKey();
        X509Ptr cert = buildSelfSignedX509(key.get(), validityDays);
 
        writeKeyToFile(key.get(), keyPath);
        writeCertToFile(cert.get(), certPath);
 
        std::filesystem::permissions(
            keyPath,
            std::filesystem::perms::owner_read | std::filesystem::perms::owner_write,
            std::filesystem::perm_options::replace);
 
        return true;
    } catch (const std::exception&) {
        
        return false;
    }
}
 
}  