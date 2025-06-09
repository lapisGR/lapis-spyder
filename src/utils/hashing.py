"""Hashing utilities for content and security."""

import hashlib
import secrets
import string
from typing import Union


def hash_content(content: Union[str, bytes]) -> str:
    """Generate SHA-256 hash of content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    
    return hashlib.sha256(content).hexdigest()


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def generate_api_key(length: int = 32) -> str:
    """Generate secure API key."""
    alphabet = string.ascii_letters + string.digits
    return "lapis_" + "".join(secrets.choice(alphabet) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """Generate secure random token."""
    return secrets.token_urlsafe(length)


def content_similarity_hash(content: str, shingle_size: int = 3) -> str:
    """Generate similarity hash for content comparison."""
    # Simple shingle-based hashing for content similarity
    content = content.lower().strip()
    
    # Remove extra whitespace
    import re
    content = re.sub(r"\s+", " ", content)
    
    # Generate shingles
    shingles = set()
    for i in range(len(content) - shingle_size + 1):
        shingle = content[i:i + shingle_size]
        shingles.add(shingle)
    
    # Create hash from sorted shingles
    sorted_shingles = sorted(shingles)
    combined = "".join(sorted_shingles)
    
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def perceptual_hash(content: str) -> str:
    """Generate perceptual hash for content structure."""
    # Extract structural elements
    import re
    
    # Count different types of HTML elements
    headings = len(re.findall(r"<h[1-6]", content, re.IGNORECASE))
    paragraphs = len(re.findall(r"<p", content, re.IGNORECASE))
    links = len(re.findall(r"<a\s", content, re.IGNORECASE))
    images = len(re.findall(r"<img", content, re.IGNORECASE))
    lists = len(re.findall(r"<[uo]l", content, re.IGNORECASE))
    
    # Create structural signature
    signature = f"{headings:03d}{paragraphs:04d}{links:03d}{images:02d}{lists:02d}"
    
    # Hash the signature
    return hashlib.md5(signature.encode()).hexdigest()[:16]