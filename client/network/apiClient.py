import hashlib 
import http.client
import json
import socket
import ssl

from typing import Any

DEFAULT_AGENT_PORT = 9443
DEFAULT_TIMEOUT = 5.0
MAX_HANDSHAKE_LINE = 512

class ApiError(Exception):

    """Ошибка HTTP-запроса или ответа RootDuck API."""
    def __inti__(self, status_code: int, detail: str):
        self.ststus_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")
     

class ConnectionError(Exception):
    """Ошибка подключения или протокола RootDuck."""


def _normalize_fingerprint(fingerprint: str) -> str:
    """Убирает разделители из SHA-256 fingerprint."""
    normalized = fingerprint.lower().replace(":", "").replace(" ", "")

    if normalized.startswith("sha256="):
        normalized = normalized[7:]

    if len(normalized) != 64:
        raise ValueError(
            "TLS fingerprint должен содержать 64 шестнадцатеричных символа"
        )

    try:
        bytes.fromhex(normalized)
    except ValueError as exc:
        raise ValueError("Некорректный TLS fingerprint") from exc

    return normalized


def get_server_fingerprint(
    host: str,
    port: int = DEFAULT_AGENT_PORT,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """
    Получает SHA-256 fingerprint TLS-сертификата сервера.

    ВАЖНО: результат сам по себе не является доказательством подлинности.
    Сверь его с fingerprint, полученным по доверенному каналу.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port), timeout=timeout) as raw_socket:
        with context.wrap_socket(
            raw_socket,
            server_hostname=host,
        ) as tls_socket:
            certificate = tls_socket.getpeercert(binary_form=True)

    if not certificate:
        raise ConnectionError("Сервер не предоставил TLS-сертификат")

    digest = hashlib.sha256(certificate).hexdigest()
    return ":".join(
        digest[index:index + 2].upper()
        for index in range(0, len(digest), 2)
    )


class _RootDuckConnection(http.client.HTTPConnection):
    """
    HTTP поверх TLS-соединения с предварительной авторизацией RootDuck.

    Порядок протокола:
    1. TLS handshake.
    2. Проверка fingerprint.
    3. Передача TOKEN: <token>.
    4. Проверка ответа OK.
    5. Обычный HTTP поверх того же TLS-соединения.
    """

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        expected_fingerprint: str,
        timeout: float,
    ):
        super().__init__(host, port=port, timeout=timeout)

        if "\n" in token or "\r" in token:
            raise ValueError("Токен содержит недопустимые символы")

        self.token = token
        self.expected_fingerprint = _normalize_fingerprint(
            expected_fingerprint
        )

    def connect(self) -> None:
        """Создаёт TLS-соединение и проходит handshake RootDuck."""
        raw_socket = socket.create_connection(
            (self.host, self.port),
            timeout=self.timeout,
        )

        tls_socket = None

        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

            # Сертификат самоподписанный, поэтому стандартная проверка CA
            # не сработает. Вместо неё проверяем точный SHA-256 fingerprint.
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            tls_socket = context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )

            certificate = tls_socket.getpeercert(binary_form=True)

            if not certificate:
                raise ConnectionError(
                    "Сервер не предоставил TLS-сертификат"
                )

            actual_fingerprint = hashlib.sha256(certificate).hexdigest()

            if actual_fingerprint != self.expected_fingerprint:
                raise ConnectionError(
                    "TLS fingerprint сервера не совпадает с сохранённым. "
                    "Соединение отклонено."
                )

            # Токен передаём только после успешной проверки сертификата.
            tls_socket.sendall(
                f"TOKEN: {self.token}\n".encode("utf-8")
            )

            # Читаем ответ строго до перевода строки, не захватывая
            # начало следующего HTTP-ответа.
            response = bytearray()

            while len(response) < MAX_HANDSHAKE_LINE:
                chunk = tls_socket.recv(1)

                if not chunk:
                    raise ConnectionError(
                        "Сервер закрыл соединение во время авторизации"
                    )

                if chunk == b"\n":
                    break

                response.extend(chunk)
            else:
                raise ConnectionError(
                    "Слишком длинный ответ handshake"
                )

            message = response.decode("utf-8", errors="replace").rstrip("\r")

            if message != "OK: connection secured":
                raise ConnectionError(
                    f"Агент отклонил соединение: {message}"
                )

            # HTTPConnection использует этот сокет для обычных HTTP-запросов.
            self.sock = tls_socket

        except Exception:
            if tls_socket is not None:
                tls_socket.close()
            else:
                raw_socket.close()
            raise


class ApiClient:
    """Клиент для взаимодействия с API домашнего сервера RootDuck."""

    def __init__(
        self,
        host: str,
        token: str,
        expected_fingerprint: str,
        port: int = DEFAULT_AGENT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        if not host.strip():
            raise ValueError("Адрес сервера не может быть пустым")

        if not token:
            raise ValueError("Токен не может быть пустым")

        self.host = host
        self.token = token
        self.port = port
        self.timeout = timeout
        self.expected_fingerprint = _normalize_fingerprint(
            expected_fingerprint
        )
        self.jwt: str | None = None

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> Any:
        """
        Выполняет HTTP-запрос через TLS-прокси RootDuck.

        method: GET, POST и другие HTTP-методы.
        path: путь API, например /auth/exchange.
        payload: JSON-тело запроса, если оно необходимо.
        authenticated: добавить Bearer JWT в заголовки.
        """
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("API path должен начинаться с одного '/'")

        method = method.upper()

        body = None
        headers = {
            "Accept": "application/json",
            "Connection": "close",
        }

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if authenticated:
            if not self.jwt:
                raise ConnectionError(
                    "JWT отсутствует. Сначала вызови exchange_token()."
                )

            headers["Authorization"] = f"Bearer {self.jwt}"

        connection = _RootDuckConnection(
            host=self.host,
            port=self.port,
            token=self.token,
            expected_fingerprint=self.expected_fingerprint,
            timeout=self.timeout,
        )

        try:
            connection.request(
                method,
                path,
                body=body,
                headers=headers,
            )

            response = connection.getresponse()
            response_body = response.read()

            if not response_body:
                data = None
            else:
                text = response_body.decode("utf-8", errors="replace")

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    data = text

            if not 200 <= response.status < 300:
                if isinstance(data, dict):
                    detail = str(data.get("detail", data))
                else:
                    detail = str(data)

                raise ApiError(response.status, detail)

            return data

        except (OSError, ssl.SSLError, http.client.HTTPException) as exc:
            raise ConnectionError(
                f"Не удалось выполнить запрос к {self.host}:{self.port}: {exc}"
            ) from exc
        finally:
            connection.close()

    def exchange_token(self) -> str:
        """Обменивает одноразовый токен на JWT."""
        response = self.request(
            method="POST",
            path="/auth/exchange",
            payload={"token": self.token},
        )

        if not isinstance(response, dict) or not response.get("jwt"):
            raise ConnectionError(
                "API вернул неожиданный ответ при обмене токена на JWT"
            )

        self.jwt = response["jwt"]
        return self.jwt

    def get(
        self,
        path: str,
        authenticated: bool = True,
    ) -> Any:
        """Выполняет GET-запрос."""
        return self.request(
            method="GET",
            path=path,
            authenticated=authenticated,
        )

    def post(
        self,
        path: str,
        payload: dict[str, Any],
        authenticated: bool = True,
    ) -> Any:
        """Выполняет POST-запрос с JSON-телом."""
        return self.request(
            method="POST",
            path=path,
            payload=payload,
            authenticated=authenticated,
        )