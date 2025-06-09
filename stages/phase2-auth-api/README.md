# Phase 2: Authentication & API

## Overview
Implement comprehensive authentication system with JWT tokens, user management, rate limiting, and core API structure.

## Duration: Week 2

## Prerequisites
- Phase 1 completed successfully
- All infrastructure services running
- Database schemas created
- Basic FastAPI app operational

## Checklist

### Day 1-2: JWT Authentication System
- [x] JWT Implementation
  - [x] Install PyJWT and dependencies
  - [x] Create JWT utility module (auth/jwt.py)
  - [x] Implement token generation function
  - [x] Implement token validation function
  - [x] Add refresh token support
  - [x] Configure token expiration times
  - [x] Handle token blacklisting in Redis
  - [x] Create custom JWT exceptions

- [x] User Model & Schema
  - [x] Create SQLAlchemy User model
  - [x] Implement password hashing with bcrypt
  - [x] Create Pydantic schemas:
    - [x] UserCreate schema
    - [x] UserResponse schema
    - [x] UserUpdate schema
    - [x] TokenResponse schema
  - [x] Add email validation
  - [x] Implement user status flags (active, verified)

### Day 2-3: Authentication Endpoints
- [x] Registration Endpoint
  - [x] POST /auth/register implementation
  - [x] Email uniqueness validation
  - [x] Password strength validation
  - [x] Generate API key for user
  - [ ] Send welcome email (optional)
  - [x] Handle registration errors
  - [x] Add rate limiting
  - [x] Write comprehensive tests

- [x] Login Endpoint
  - [x] POST /auth/login implementation
  - [x] Validate credentials
  - [x] Generate access and refresh tokens
  - [x] Track login attempts
  - [ ] Implement account lockout after failures
  - [x] Log successful logins
  - [x] Return user profile with tokens
  - [x] Write tests for all scenarios

- [x] Token Management
  - [x] POST /auth/refresh endpoint
  - [x] POST /auth/logout endpoint
  - [x] GET /auth/me endpoint
  - [x] Implement token revocation
  - [x] Add token introspection
  - [x] Handle expired tokens gracefully

### Day 3-4: Authorization & Middleware
- [x] FastAPI Dependencies
  - [x] Create get_current_user dependency
  - [x] Create require_auth dependency
  - [x] Implement role-based access control
  - [x] Add permission decorators
  - [x] Create API key authentication option
  - [x] Handle authentication in swagger UI

- [x] Middleware Implementation
  - [x] Create authentication middleware
  - [x] Add request context with user info
  - [x] Implement audit logging
  - [x] Add security headers
  - [x] Create request/response logging

### Day 4-5: Rate Limiting & API Keys
- [x] Rate Limiting System
  - [x] Implement Redis-based rate limiter
  - [x] Create rate limit decorator
  - [x] Configure limits per endpoint
  - [x] Add user-specific rate limits
  - [x] Implement sliding window algorithm
  - [x] Return rate limit headers
  - [x] Handle rate limit exceeded errors
  - [x] Create bypass for certain API keys

- [x] API Key Management
  - [x] Generate secure API keys
  - [x] Create API key endpoints:
    - [x] POST /auth/api-keys
    - [x] GET /auth/api-keys
    - [x] DELETE /auth/api-keys/{key_id}
  - [x] Implement key rotation
  - [x] Add key usage tracking
  - [x] Set key permissions/scopes
  - [x] Create separate rate limits for API keys

### Day 5: Security Hardening
- [x] Security Measures
  - [x] Implement CORS properly
  - [x] Add CSRF protection
  - [x] Set secure cookie flags
  - [x] Implement request signing
  - [x] Add SQL injection prevention
  - [x] Validate all inputs with Pydantic
  - [x] Implement timeout handling
  - [x] Add brute force protection

- [x] Testing & Documentation
  - [x] Write unit tests for all auth functions
  - [x] Create integration tests for auth flow
  - [x] Test rate limiting thoroughly
  - [x] Document all endpoints with OpenAPI
  - [ ] Create Postman collection
  - [ ] Write security best practices guide
  - [x] Perform basic security audit

## Deliverables
1. Complete JWT authentication system
2. User registration and login endpoints
3. Rate limiting implementation
4. API key management system
5. Comprehensive test suite
6. API documentation

## Validation Criteria
- [ ] Users can register with valid emails
- [ ] Login returns valid JWT tokens
- [ ] Protected endpoints require authentication
- [ ] Rate limiting blocks excessive requests
- [ ] API keys work as alternative auth
- [ ] All security tests pass
- [ ] No SQL injection vulnerabilities
- [ ] Tokens expire and refresh correctly

## API Endpoints Summary
```
POST   /auth/register          - Register new user
POST   /auth/login            - Login user
POST   /auth/refresh          - Refresh access token
POST   /auth/logout           - Logout user
GET    /auth/me              - Get current user
PUT    /auth/me              - Update current user
POST   /auth/api-keys        - Create API key
GET    /auth/api-keys        - List user's API keys
DELETE /auth/api-keys/{id}   - Delete API key
POST   /auth/forgot-password - Request password reset
POST   /auth/reset-password  - Reset password
```

## Common Issues & Solutions
1. **JWT Secret Key**: Must be strong and environment-specific
2. **Token Storage**: Never store in localStorage for production
3. **CORS Issues**: Configure allowed origins carefully
4. **Rate Limit Bypass**: Ensure it can't be bypassed with headers
5. **Password Requirements**: Balance security with usability

## Security Checklist
- [ ] Passwords hashed with bcrypt (cost factor 12+)
- [ ] JWT secret key at least 256 bits
- [ ] Tokens expire in reasonable time
- [ ] Failed login attempts tracked
- [ ] Rate limiting on all endpoints
- [ ] Input validation on all fields
- [ ] SQL injection prevention verified
- [ ] XSS prevention in place
- [ ] CSRF tokens implemented
- [ ] Security headers configured

## Testing Guide
```bash
# Run auth tests
pytest tests/test_auth.py -v

# Test registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Test protected endpoint
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Test rate limiting
for i in {1..100}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "wrong"}' &
done
```

## Next Phase Dependencies
Authentication system must be fully functional before implementing crawling endpoints in Phase 3.