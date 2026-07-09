import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

security = HTTPBearer()



# Initialize Enkrypt Client
_enkrypt_client = None
_enkrypt_key = settings.ENKRYPTAI_API_KEY
if _enkrypt_key and _enkrypt_key != "mock-enkrypt-key":
    try:
        from enkryptai_sdk import GuardrailsClient
        _enkrypt_client = GuardrailsClient(api_key=_enkrypt_key)
    except Exception as e:
        print(f"Error initializing Enkrypt GuardrailsClient: {e}")

def _get_fernet(key: str) -> Any:
    """Derive a 32-byte Fernet key from settings.SECRET_KEY."""
    import hashlib
    import base64
    from cryptography.fernet import Fernet
    key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

class EnkryptMiddleware:
    """
    Enkrypt Middleware Abstraction:
    Provides custom payload field encryption/decryption (AES key wrapper)
    to encrypt highly sensitive environmental fields (such as access tokens, passwords, and private API keys)
    before saving them in persistent storage or database logs, as well as checking system payload integrity.
    """
    @staticmethod
    def encrypt_data(plain_text: str, key: str = settings.SECRET_KEY) -> str:
        """
        Encrypts sensitive fields like access keys, environmental configurations, or logs
        using production-grade Fernet symmetric encryption.
        """
        try:
            f = _get_fernet(key)
            return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')
        except Exception:
            return plain_text

    @staticmethod
    def decrypt_data(cipher_text: str, key: str = settings.SECRET_KEY) -> str:
        """
        Decrypts sensitive fields back to standard unicode plain_text.
        """
        try:
            f = _get_fernet(key)
            return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
        except Exception:
            # Fallback to avoid breaking on plaintext or old XOR-encrypted entries
            try:
                import base64
                raw_bytes = base64.b64decode(cipher_text.encode('utf-8'))
                key_cycled = (key * (len(raw_bytes) // len(key) + 1))[:len(raw_bytes)]
                plain_bytes = bytes([b1 ^ ord(b2) for b1, b2 in zip(raw_bytes, key_cycled)])
                return plain_bytes.decode('utf-8')
            except Exception:
                return cipher_text

    @staticmethod
    def validate_input(input_text: str) -> Dict[str, Any]:
        """
        Scan input text for security and compliance threats using official Enkrypt Sentry API,
        with fallback to local regex-based scanning.
        """
        global _enkrypt_client
        if _enkrypt_client:
            try:
                from enkryptai_sdk import GuardrailsConfig
                config = GuardrailsConfig()
                config.update(
                    pii={"enabled": True, "entities": ["secrets", "email", "phone_number", "ssn", "credit_card"]},
                    injection_attack={"enabled": True},
                    policy_violation={"enabled": True}
                )
                response = _enkrypt_client.detect(input_text, config=config)
                if response.has_violations():
                    violations = response.get_violations()
                    mapped_threats = []
                    for v in violations:
                        if v == "injection_attack":
                            mapped_threats.append("Potential Prompt Injection Attack Detected")
                        elif v == "pii":
                            mapped_threats.append("Potential Personal Identifiable Information (PII) / Secret Leak")
                        elif v == "policy_violation":
                            mapped_threats.append("Potential Policy Violation")
                        else:
                            mapped_threats.append(f"Security Alert: {v}")
                    return {"status": "ALERT", "threats": mapped_threats, "sanitized": True}
                return {"status": "PASSED", "threats": [], "sanitized": False}
            except Exception as e:
                print(f"Enkrypt API validation error: {e}. Falling back to local regex scanner.")

        # Fallback local regex scanning
        import re
        threats = []
        
        # SQL Injection patterns
        sql_patterns = [
            r"(?i)\bUNION\b.*\bSELECT\b",
            r"(?i)\bSELECT\b.*\bFROM\b",
            r"(?i)'\s*OR\s*'\d+'\s*=\s*'\d+",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, input_text):
                threats.append("Potential SQL Injection Pattern Detected")
                
        # Secrets/Credentials patterns
        credential_patterns = [
            r"(?i)(password|passwd|pass|pwd|secret|token|api_key|apikey|private_key)\s*[:=\s]+[a-zA-Z0-9_\-\.\~]{8,}",
            r"AIzaSy[a-zA-Z0-9_\-]{33}",  # Google API key pattern
        ]
        for pattern in credential_patterns:
            if re.search(pattern, input_text):
                threats.append("Potential Sensitive Credential/Key Exposure")
                
        # PII (SSN, credit cards)
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b(?:\d[ -]*?){13,16}\b",  # Credit Card
        ]
        for pattern in pii_patterns:
            if re.search(pattern, input_text):
                threats.append("Potential Personal Identifiable Information (PII) Leak")
                
        if threats:
            return {"status": "ALERT", "threats": threats, "sanitized": True}
        return {"status": "PASSED", "threats": [], "sanitized": False}

    @staticmethod
    def validate_output(output_text: str) -> Dict[str, Any]:
        """
        Scan output text generated by LLM for potential credentials leak or toxic hallucinated secrets.
        """
        global _enkrypt_client
        if _enkrypt_client:
            try:
                from enkryptai_sdk import GuardrailsConfig
                config = GuardrailsConfig()
                config.update(
                    pii={"enabled": True, "entities": ["secrets", "email", "phone_number", "ssn", "credit_card"]},
                    toxicity={"enabled": True}
                )
                response = _enkrypt_client.detect(output_text, config=config)
                if response.has_violations():
                    violations = response.get_violations()
                    mapped_threats = []
                    for v in violations:
                        if v == "pii":
                            mapped_threats.append("Leaked Cryptographic Material / Key in LLM Generation")
                        elif v == "toxicity":
                            mapped_threats.append("Toxic or Unsafe Content Generated by LLM")
                        else:
                            mapped_threats.append(f"Security Alert: {v}")
                    return {"status": "ALERT", "threats": mapped_threats, "sanitized": True}
                return {"status": "PASSED", "threats": [], "sanitized": False}
            except Exception as e:
                print(f"Enkrypt API validation error: {e}. Falling back to local regex scanner.")

        # Fallback local regex scanning
        import re
        threats = []
        
        # Similar password/secret leaks in output
        secret_patterns = [
            r"(?i)(password|secret|token|private_key|api_key)\s*[:=\s]+[a-zA-Z0-9_\-\.\~]{10,}",
        ]
        for pattern in secret_patterns:
            if re.search(pattern, output_text):
                threats.append("Leaked Cryptographic Material / Key in LLM Generation")
                
        if threats:
            return {"status": "ALERT", "threats": threats, "sanitized": True}
        return {"status": "PASSED", "threats": [], "sanitized": False}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Refresh tokens expire in 7 days by default
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise jwt.PyJWTError("Not a valid refresh token type")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Make sure this is an access token, not a refresh token
        if payload.get("type") == "refresh":
            raise credentials_exception
            
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise credentials_exception
        return {"email": email, "role": role, "name": payload.get("name", "Unknown SRE")}
    except jwt.PyJWTError:
        raise credentials_exception


def require_role(allowed_roles: list):
    def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user
    return dependency
