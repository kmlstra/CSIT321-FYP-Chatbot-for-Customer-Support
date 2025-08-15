# Environment Switch Guide

This project includes an enhanced environment switching system that allows you to easily toggle between localhost development and AWS production environments.

## Available Scripts

### Enhanced Switch Script (Recommended)
```powershell
./switch-environment.ps1 -Environment <local|aws|production>
```

**Examples:**
- Switch to localhost: `./switch-environment.ps1 -Environment local`
- Switch to AWS: `./switch-environment.ps1 -Environment aws`
- Switch to production: `./switch-environment.ps1 -Environment production`

### Legacy Scripts (Still Available)
- `./switch-to-local.ps1` - Switch to localhost development
- `./switch-to-aws.ps1` - Switch to AWS production

## What Gets Configured

The switch scripts automatically configure:

### Backend Configuration (`backend/.env`)
- `DOMAIN` - Base domain for all services
- `NEXT_PUBLIC_DOMAIN` - Frontend-accessible domain
- `BACKEND_PORT` and `NEXT_PUBLIC_BACKEND_PORT` - Backend service port (8000)
- `NEXT_PUBLIC_ENV` - Environment type (development/production)
- `PROFILE_PICTURE_URL` - Profile picture URL with correct domain
- `DEBUG` - Debug mode (true for local, false for production)

### Frontend Configuration (`frontend/.env.local`)
- `NODE_ENV` - Node environment
- `NEXT_PUBLIC_DOMAIN` - Base domain
- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_RASA_URL` - RASA service URL
- `NEXT_PUBLIC_WIDGET_URL` - Widget base URL
- `NEXT_PUBLIC_FRONTEND_URL` - Frontend URL
- `NEXT_PUBLIC_BACKEND_URL` - Backend URL
- `NEXT_PUBLIC_DEBUG` - Debug mode
- `NEXT_PUBLIC_ENV` - Environment type
- `PROFILE_PICTURE_URL` - Profile picture URL

## Environment Configurations

### Local Development
- **Domain:** `http://localhost`
- **Backend Port:** `8000`
- **Environment:** `development`
- **Debug:** `true`
- **Profile Picture:** `http://localhost:8000/static/boy.png`

### AWS Production
- **Domain:** `http://54.254.180.103`
- **Backend Port:** `8000`
- **Environment:** `production`
- **Debug:** `false`
- **Profile Picture:** `http://54.254.180.103:8000/static/boy.png`

## Usage Workflow

1. **Switch Environment:**
   ```powershell
   ./switch-environment.ps1 -Environment local
   ```

2. **Start Services:**
   ```powershell
   npm run dev:all
   ```

3. **Access Application:**
   - Frontend: Check the displayed URL after switching
   - Backend API: Check the displayed API URL
   - Test Widget: Use the provided test widget URL

## Key Features

- ✅ **Unified Configuration:** Single script handles both backend and frontend
- ✅ **Port Consistency:** Maintains correct port 8000 for backend in both environments
- ✅ **Complete Variable Set:** Includes all necessary environment variables
- ✅ **Clear Feedback:** Displays access points and configuration summary
- ✅ **Error Handling:** Provides clear error messages if issues occur
- ✅ **Backward Compatibility:** Legacy scripts still work

## Troubleshooting

If you encounter issues:

1. **Permission Errors:** Run PowerShell as Administrator
2. **Execution Policy:** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. **File Not Found:** Ensure you're in the project root directory
4. **Configuration Issues:** Check that both `backend/.env` and `frontend/.env.local` files exist after switching

## Notes

- The system automatically creates the `frontend/.env.local` file if it doesn't exist
- All URLs use the correct ports for each environment
- The profile picture URL is automatically updated to match the current environment
- MongoDB Atlas connection remains the same across all environments