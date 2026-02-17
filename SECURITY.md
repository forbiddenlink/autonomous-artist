# Security Best Practices

## Overview
This document outlines the security measures implemented in the Autonomous Artist application and best practices for deployment.

## Implemented Security Features

### 1. Rate Limiting
- **Flask-Limiter** restricts API request frequency
- Default: 200 requests/day, 50 requests/hour
- Paint endpoint: 10 requests/hour (AI generation is expensive)
- Health check: 30 requests/minute

### 2. CORS (Cross-Origin Resource Sharing)
- Configured via `ALLOWED_ORIGINS` environment variable
- **Production**: Set to specific domains (e.g., `https://yourdomain.com`)
- **Development**: Can use `*` but not recommended

### 3. Security Headers
- **Flask-Talisman** adds security headers:
  - Content Security Policy (CSP)
  - X-Frame-Options
  - X-Content-Type-Options
  - Strict-Transport-Security (HSTS)
- Only enabled when `DEBUG=False`

### 4. Input Validation
- All user inputs are validated and sanitized
- Prompt validation prevents injection attacks
- File path validation prevents directory traversal
- JSON validation for API requests

### 5. Environment Variables
- Sensitive credentials stored in `.env` file
- `.env` file excluded from git via `.gitignore`
- Use `.env.example` as a template

### 6. API Token Security
- HuggingFace API token required for AI features
- Tokens validated before use
- Never log or expose tokens in responses

## Deployment Checklist

### Before Deploying to Production:

1. **Environment Variables**
   ```bash
   # Run the production readiness check
   python3 production_check.py
   ```

2. **Set Critical Variables**
   - `DEBUG=False` (CRITICAL!)
   - `HF_API_TOKEN=your_actual_token`
   - `ALLOWED_ORIGINS=https://yourdomain.com`
   - `IMGUR_CLIENT_ID=your_imgur_client_id`

3. **Enable HTTPS**
   - Set `force_https=True` in Talisman configuration
   - Use a reverse proxy (nginx, Apache) with SSL certificate
   - Use Let's Encrypt for free SSL certificates

4. **Database/Storage Security**
   - Ensure `artist_memory.json` has appropriate permissions
   - Consider using a proper database for production
   - Regular backups of memory and generated art

5. **Monitoring & Logging**
   - Set `LOG_LEVEL=WARNING` or `ERROR` in production
   - Monitor logs for suspicious activity
   - Set up alerting for rate limit violations

6. **Dependencies**
   ```bash
   # Update all dependencies
   pip install --upgrade -r requirements.txt
   
   # Check for security vulnerabilities
   pip install safety
   safety check
   ```

## Common Security Issues

### 1. Debug Mode in Production
**Risk**: Exposes sensitive information and allows code execution
**Fix**: Always set `DEBUG=False` in production

### 2. Weak CORS Policy
**Risk**: Allows unauthorized domains to access your API
**Fix**: Set `ALLOWED_ORIGINS` to specific domains

### 3. Missing Rate Limiting
**Risk**: DDoS attacks and API abuse
**Fix**: Already implemented, but monitor and adjust limits

### 4. Exposed API Keys
**Risk**: Unauthorized use of your HuggingFace/Facebook accounts
**Fix**: Use environment variables, never commit to git

### 5. Unvalidated Input
**Risk**: Injection attacks and data corruption
**Fix**: Already implemented validation, keep it updated

## API Endpoint Security

### Protected Endpoints
All `/api/*` endpoints are protected with:
- Rate limiting
- CORS restrictions
- Input validation
- Error handling that doesn't expose internals

### `/api/paint` - High Security
- Strictest rate limit (10/hour)
- Input validation for all parameters
- Prompt sanitization
- Result caching to reduce API calls

### `/health` - Monitoring
- Less strict rate limit (30/minute)
- No sensitive data in response
- Useful for uptime monitoring

## Incident Response

### If You Suspect a Security Breach:

1. **Immediately**:
   - Rotate all API tokens (HuggingFace, Facebook, Imgur)
   - Check logs for suspicious activity
   - Temporarily disable the application if needed

2. **Investigation**:
   - Review access logs
   - Check for unusual API usage patterns
   - Verify integrity of generated content

3. **Recovery**:
   - Update all credentials
   - Patch any vulnerabilities
   - Deploy updated version
   - Monitor closely for 48 hours

## Regular Maintenance

### Weekly
- Review application logs
- Check cache size and cleanup if needed
- Monitor API usage and costs

### Monthly
- Update dependencies
- Run security audit (safety check)
- Review and rotate API tokens
- Test backup and recovery procedures

### Quarterly
- Full security review
- Penetration testing (if budget allows)
- Update security policies
- Train team on new threats

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [HuggingFace Token Security](https://huggingface.co/docs/hub/security-tokens)

## Contact

For security concerns, please review the code and create issues on GitHub (if open source) or contact the maintainer directly.
