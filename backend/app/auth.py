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
    Provides custom payload field encryption/decryption and official Enkrypt AI integration
    for role-based security guardrails across inputs, outputs, and documents.
    """
    @staticmethod
    def encrypt_data(plain_text: str, key: str = settings.SECRET_KEY) -> str:
        try:
            f = _get_fernet(key)
            return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')
        except Exception:
            return plain_text

    @staticmethod
    def decrypt_data(cipher_text: str, key: str = settings.SECRET_KEY) -> str:
        try:
            f = _get_fernet(key)
            return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
        except Exception:
            try:
                import base64
                raw_bytes = base64.b64decode(cipher_text.encode('utf-8'))
                key_cycled = (key * (len(raw_bytes) // len(key) + 1))[:len(raw_bytes)]
                plain_bytes = bytes([b1 ^ ord(b2) for b1, b2 in zip(raw_bytes, key_cycled)])
                return plain_bytes.decode('utf-8')
            except Exception:
                return cipher_text

    @staticmethod
    def _log_security_event(db, user_id: str, action: str, threats: list, text: str):
        if not db: return
        try:
            from app.models.audit_log import AuditLog
            log = AuditLog(
                userId=user_id,
                action=action,
                resourceType="Enkrypt Guardrails",
                details={"threats": threats, "snippet": text[:100] + "..." if len(text) > 100 else text},
                response_status="BLOCKED"
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"Failed to log security event: {e}")

    @staticmethod
    def _get_role_config(role: str, is_output: bool = False, is_document: bool = False):
        from enkryptai_sdk import GuardrailsConfig
        config = GuardrailsConfig()
        
        # Determine strictness
        is_strict = role in ["Viewer", "DevOps"]
        
        if is_document:
            config.update(
                pii={"enabled": True, "entities": ["secrets", "email", "phone_number", "ssn", "credit_card"], "redact": True},
                toxicity={"enabled": True},
                policy_violation={"enabled": True}
            )
            return config

        if is_output:
            if is_strict:
                config.update(
                    pii={"enabled": True, "entities": ["secrets", "email", "phone_number", "ssn", "credit_card"], "redact": True},
                    toxicity={"enabled": True}
                )
            else:
                config.update(
                    pii={"enabled": True, "entities": ["secrets"], "redact": False},
                    toxicity={"enabled": True}
                )
        else:
            if is_strict:
                config.update(
                    pii={"enabled": True, "entities": ["secrets", "email", "phone_number", "ssn", "credit_card"]},
                    injection_attack={"enabled": True},
                    policy_violation={"enabled": True}
                )
            else:
                config.update(
                    pii={"enabled": True, "entities": ["secrets"]},
                    injection_attack={"enabled": True},
                    policy_violation={"enabled": True}
                )
        return config

    @staticmethod
    def validate_input(input_text: str, current_user: dict = None, db = None) -> Dict[str, Any]:
        global _enkrypt_client
        role = current_user.get("role", "Viewer") if current_user else "Viewer"
        user_id = current_user.get("email", "anonymous") if current_user else "anonymous"

        if _enkrypt_client:
            try:
                config = EnkryptMiddleware._get_role_config(role, is_output=False)
                response = _enkrypt_client.detect(input_text, config=config)
                if response.has_violations():
                    violations = response.get_violations()
                    mapped_threats = [f"Security Alert: {v}" for v in violations]
                    EnkryptMiddleware._log_security_event(db, user_id, "ENKRYPT_INPUT_BLOCK", mapped_threats, input_text)
                    return {"status": "ALERT", "threats": mapped_threats, "sanitized": True}
                return {"status": "PASSED", "threats": [], "sanitized": False}
            except Exception as e:
                print(f"Enkrypt API error: {e}. Fallback to regex.")

        # Fallback
        import re
        threats = []
        sql_patterns = [r"(?i)\bUNION\b.*\bSELECT\b", r"(?i)\bSELECT\b.*\bFROM\b", r"(?i)'\s*OR\s*'\d+'\s*=\s*'\d+"]
        for p in sql_patterns:
            if re.search(p, input_text): threats.append("Potential SQL Injection")
        
        credential_patterns = [r"(?i)(password|secret|api_key)\s*[:=\s]+[a-zA-Z0-9_\-\.\~]{8,}", r"AIzaSy[a-zA-Z0-9_\-]{33}"]
        for p in credential_patterns:
            if re.search(p, input_text): threats.append("Credential Exposure")
            
        if threats:
            EnkryptMiddleware._log_security_event(db, user_id, "ENKRYPT_INPUT_BLOCK_FALLBACK", threats, input_text)
            return {"status": "ALERT", "threats": threats, "sanitized": True}
        return {"status": "PASSED", "threats": [], "sanitized": False}

    @staticmethod
    def validate_output(output_text: str, current_user: dict = None, db = None) -> Dict[str, Any]:
        global _enkrypt_client
        role = current_user.get("role", "Viewer") if current_user else "Viewer"
        user_id = current_user.get("email", "anonymous") if current_user else "anonymous"

        if _enkrypt_client:
            try:
                config = EnkryptMiddleware._get_role_config(role, is_output=True)
                response = _enkrypt_client.detect(output_text, config=config)
                if response.has_violations():
                    violations = response.get_violations()
                    mapped_threats = [f"Security Alert: {v}" for v in violations]
                    EnkryptMiddleware._log_security_event(db, user_id, "ENKRYPT_OUTPUT_BLOCK", mapped_threats, output_text)
                    return {"status": "ALERT", "threats": mapped_threats, "sanitized": True}
                return {"status": "PASSED", "threats": [], "sanitized": False}
            except Exception as e:
                print(f"Enkrypt API error: {e}. Fallback to regex.")

        import re
        threats = []
        secret_patterns = [r"(?i)(password|secret|private_key|api_key)\s*[:=\s]+[a-zA-Z0-9_\-\.\~]{10,}"]
        for p in secret_patterns:
            if re.search(p, output_text): threats.append("Leaked Cryptographic Material")
                
        if threats:
            EnkryptMiddleware._log_security_event(db, user_id, "ENKRYPT_OUTPUT_BLOCK_FALLBACK", threats, output_text)
            return {"status": "ALERT", "threats": threats, "sanitized": True}
        return {"status": "PASSED", "threats": [], "sanitized": False}

    @staticmethod
    def scan_document(document_text: str, current_user: dict = None, db = None) -> Dict[str, Any]:
        """Scans uploaded documents and incidents for secrets, toxicity, and leakage."""
        global _enkrypt_client
        role = current_user.get("role", "SRE") if current_user else "SRE"
        user_id = current_user.get("email", "anonymous") if current_user else "anonymous"

        if _enkrypt_client:
            try:
                config = EnkryptMiddleware._get_role_config(role, is_document=True)
                response = _enkrypt_client.detect(document_text, config=config)
                
                # Retrieve redacted text if applicable
                sanitized_text = document_text
                try:
                    if hasattr(response, 'text'): sanitized_text = response.text
                except Exception:
                    pass

                if response.has_violations():
                    violations = response.get_violations()
                    mapped_threats = [f"Document Security Alert: {v}" for v in violations]
                    EnkryptMiddleware._log_security_event(db, user_id, "ENKRYPT_DOCUMENT_QUARANTINE", mapped_threats, document_text)
                    return {"status": "QUARANTINED", "threats": mapped_threats, "sanitized_text": sanitized_text}
                return {"status": "PASSED", "threats": [], "sanitized_text": document_text}
            except Exception as e:
                print(f"Enkrypt API error on document scan: {e}")

        # Fallback
        import re
        threats = []
        if re.search(r"(?i)(password|secret|private_key)\s*[:=\s]+[a-zA-Z0-9_\-\.\~]{10,}", document_text):
            threats.append("Leaked Secrets")
        if threats:
            EnkryptMiddleware._log_security_event(db, user_id, "ENKRYPT_DOCUMENT_QUARANTINE_FALLBACK", threats, document_text)
            return {"status": "QUARANTINED", "threats": threats, "sanitized_text": document_text}
        return {"status": "PASSED", "threats": [], "sanitized_text": document_text}


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

ROLE_PERMISSIONS = {
    "Admin": ["*"],
    "SRE": [
        "incidents:read", "incidents:write",
        "logs:read", "agents:execute", "reports:read", "reports:write", "knowledge:read"
    ],
    "Security Analyst": [
        "incidents:read", "logs:read", "audit:read", "security:write", "reports:read", "knowledge:read"
    ],
    "DevOps": [
        "incidents:read", "incidents:write", "logs:read", "agents:execute", "knowledge:read"
    ],
    "Knowledge Manager": [
        "incidents:read", "knowledge:read", "knowledge:write", "reports:read"
    ],
    "Viewer": [
        "incidents:read", "logs:read", "reports:read", "knowledge:read"
    ]
}

def require_permission(required_permission: str):
    def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        role = current_user.get("role", "Viewer")
        user_permissions = ROLE_PERMISSIONS.get(role, [])
        if "*" not in user_permissions and required_permission not in user_permissions:
            # We could also log a forbidden access attempt here
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required permission: {required_permission}"
            )
        return current_user
    return dependency
