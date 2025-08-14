# RASA Dynamic Configuration System

This document explains the dynamic configuration system for RASA endpoints that allows seamless switching between localhost development and production deployment environments.

## Overview

The system automatically generates the `endpoints.yml` file based on environment variables, eliminating the need to manually edit configuration files when switching between environments.

## How It Works

1. **Environment Variables**: Configuration is controlled through the `.env` file
2. **Dynamic Generation**: The `start_rasa.py` script automatically generates `endpoints.yml` before starting RASA
3. **Template System**: A template file (`endpoints.yml.template`) serves as the base configuration

## Key Files

- **`.env`**: Contains environment variables including `DOMAIN` and `RASA_ACTIONS_PORT`
- **`start_rasa.py`**: Loads environment variables, expands URLs, and generates `endpoints.yml`
- **`endpoints.yml`**: Auto-generated file (DO NOT EDIT MANUALLY)
- **`endpoints.yml.template`**: Template for the endpoints configuration

## Environment Configuration

### For Localhost Development
```bash
# In backend/.env
DOMAIN=http://localhost
RASA_ACTIONS_PORT=5055
RASA_ACTION_ENDPOINT_URL=${DOMAIN}:${RASA_ACTIONS_PORT}/webhook
```

This generates:
```yaml
# endpoints.yml
action_endpoint:
  url: "http://localhost:5055/webhook"
```

### For Production Deployment
```bash
# In backend/.env
DOMAIN=http://54.254.180.103  # Replace with your actual domain/IP
RASA_ACTIONS_PORT=5055
RASA_ACTION_ENDPOINT_URL=${DOMAIN}:${RASA_ACTIONS_PORT}/webhook
```

This generates:
```yaml
# endpoints.yml
action_endpoint:
  url: "http://54.254.180.103:5055/webhook"
```

## How to Switch Environments

1. **Edit the `.env` file**: Change the `DOMAIN` variable to your target environment
2. **Restart RASA**: Run `npm run dev:all` or restart the RASA server
3. **Automatic Configuration**: The system will automatically generate the correct `endpoints.yml`

## Benefits

- **No Manual Editing**: Never need to manually edit `endpoints.yml`
- **Environment Agnostic**: Same codebase works in any environment
- **Error Prevention**: Eliminates configuration mistakes when switching environments
- **Version Control Friendly**: Only environment variables change, not configuration files

## Troubleshooting

### Issue: RASA shows InvalidURL errors
**Solution**: Ensure the `.env` file has the correct `DOMAIN` value and restart RASA

### Issue: Actions not working
**Solution**: 
1. Check that RASA Actions server is running on the configured port
2. Verify the `DOMAIN` and `RASA_ACTIONS_PORT` in `.env`
3. Restart both RASA server and Actions server

### Issue: endpoints.yml not updating
**Solution**: The file is generated each time `start_rasa.py` runs. Restart the RASA server to regenerate.

## Development Workflow

1. **Local Development**: Keep `DOMAIN=http://localhost` in `.env`
2. **Testing**: Use `npm run dev:all` to start all services
3. **Deployment**: Update `DOMAIN` to production URL before deployment
4. **Verification**: Check generated `endpoints.yml` has correct URLs

## Important Notes

- **Never edit `endpoints.yml` directly** - it will be overwritten
- **Always use the `.env` file** for configuration changes
- **The system supports any domain/IP** - just update the `DOMAIN` variable
- **HTTPS is supported** - use `DOMAIN=https://yourdomain.com`