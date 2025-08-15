# CleverCompanion - Singapore Automotive Chatbot

A comprehensive chatbot platform for automotive customer support using RASA, FastAPI, and Next.js.

## 📋 Prerequisites

### For Docker Deployment:
- Docker Desktop
- 8GB+ RAM
- Git

### For Development:
- Python 3.8+
- Node.js 18+
- Git
- MongoDB Atlas account (cloud database)

## 🗄️ Database Configuration

### MongoDB Atlas Setup
This project uses **MongoDB Atlas** (cloud database) instead of local MongoDB:

1. **Create MongoDB Atlas Account**: Sign up at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. **Create Cluster**: Set up a free cluster (M0 Sandbox)
3. **Get Connection String**: Copy your connection string from Atlas dashboard
4. **Configure Environment**: Update `backend/.env` file:
   ```env
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database
   MONGODB_DB=automotive_chatbot_saas
   ```

**Note**: No local MongoDB installation required - all data is stored in Atlas cloud.

## 🛠️ Installation

### Docker Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd automotive_chatbot
   ```

2. **Run Docker setup:**
   ```bash
   cd deploy
   # Windows
   .\docker-start.bat
   # Linux/Mac
   ./docker-start.sh
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - RASA API: http://localhost:5005

### Manual Development Setup

#### Backend Setup

For development with hot reloading:

## 🚗 Overview
CleverCompanion is an advanced automotive chatbot platform specifically designed for Singapore's car market, featuring real-time COE prices, vehicle recommendations, test drive booking, and comprehensive automotive services.

## 🏗️ Architecture

### Frontend (React + Next.js)
- **Main Chat Interface**: `localhost:3000`
- **Admin Dashboard**: `localhost:3000/dashboard` 
- **Embeddable Widget**: `clevercompanion-widget.js`

### Backend (FastAPI + RASA)
- **API Server**: `localhost:8000`
- **RASA NLU**: `localhost:5005`
- **RASA Actions**: `localhost:5055`

### BCE Framework Implementation
- **Boundaries**: HTTP API endpoints (`/api/coe`, `/api/vehicles`)
- **Controllers**: Business logic orchestration
- **Entities**: Data models and structures
- **External**: RASA actions call through boundaries only

## 🎯 Core Features

### 💰 COE Price Service
- Real-time COE bidding results
- Category-wise pricing (A, B, C, D, E)
- Historical trends and analysis
- Smart buying recommendations

### 🚗 Vehicle Services
- Comprehensive vehicle database
- Brand and model recommendations
- Pricing calculations (Car + COE + fees)
- Feature comparisons

### 💳 Financing Services
- Interactive loan calculator
- Multiple bank rate comparisons
- Down payment scenarios
- Monthly payment calculations

### 📅 Booking Services
- Test drive scheduling
- Service appointment booking
- Sales consultation booking
- Emergency assistance

### 🔧 Maintenance Support
- Singapore-specific maintenance schedules
- Climate-adapted recommendations
- Cost estimates and budgeting
- Service provider recommendations

### 💬 Conversation Storage
- **Unified Conversations**: All messages consolidated into single entries per conversation ID
- **Local Timestamps**: Singapore timezone (UTC+8) with ISO format (e.g., `2025-08-02T11:42:47.152000+08:00`)
- **Message Consolidation**: User messages, system actions, and bot responses appended to one conversation record
- **Automatic Logging**: All RASA actions automatically logged through `AutoLoggedAction` base class
- **MongoDB Integration**: Efficient storage with proper indexing for conversation retrieval
- **Real-time Updates**: Messages instantly appended to existing conversations
- **Chat History Viewer**: Standalone page for live support to view conversation history by ID

### 🎧 Live Support Features
- **Chat History Viewer**: `localhost:3000/chat-history-viewer.html`
- **Conversation Search**: Search by conversation ID for support agents
- **Supabase Integration**: Ready for integration with existing Supabase infrastructure
- **Real-time Support**: View complete conversation history with timestamps

## 🔧 Recent Fixes & Updates

### ✅ RASA Action Registration Fix
- **Issue**: `RasaException: Failed to execute custom action 'action_contact_us'`
- **Solution**: Updated `rasa_actions.py` to properly import and register contact actions
- **Actions Fixed**: `action_contact_us`, `action_store_location`, `action_operating_hours`, `action_provide_business_hours`
- **Status**: ✅ All contact actions now properly registered

### ✅ Chat History Viewer
- **Feature**: New standalone page for live support agents
- **Location**: `localhost:3000/chat-history-viewer.html`
- **Integration**: Supabase-ready with comprehensive integration guide
- **Status**: ✅ Ready for production use

## 📊 Service Status

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| Frontend | 3000 | ✅ Active | React application |
| Backend API | 8000 | ✅ Active | FastAPI services |
| RASA NLU | 5005 | ✅ Active | Natural language understanding |
| RASA Actions | 5055 | ✅ Active | Custom business logic |

## 🚀 Quick Start

### Prerequisites
- **Python 3.9.13** (RASA 3.6.4 compatible)
- **Node.js 18+** and **npm**
- **Git**
- **MongoDB Atlas account** (cloud database - no local MongoDB required)
- **Good internet connection** (for RASA installation)
- **5GB+ free disk space**

## 🐳 Docker Deployment

### Local Development

**Start all services:**
```bash
cd deploy
# Windows
.\docker-start.bat
# Linux/Mac
./docker-start.sh
```

**Manage services:**
```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart services
docker compose restart

# Rebuild images
docker compose build --no-cache
```

### 🌐 AWS EC2 Production Deployment

**🚀 Streamlined AWS EC2 Deployment**

Deploy to AWS EC2 using our unified deployment script:

**Prerequisites:**
- Docker Desktop installed and running
- SSH access to EC2 instance: `54.254.180.103`
- SSH key file: `cc.pem` (place in project root)

**Single Command Deployment:**
```powershell
# Deploy to AWS EC2 with automatic Docker build and deployment
.\deploy-to-ec2.ps1 -EC2Host "54.254.180.103"
```

**What the script does:**
1. Builds Docker images locally (frontend, backend, RASA)
2. Saves images as compressed tar files
3. Copies images and configuration to EC2 via SSH
4. Loads images and starts containers on EC2
5. Performs health checks and cleanup

**Access your deployed application:**
- Frontend: `http://54.254.180.103`
- Test Widget: `http://54.254.180.103/test-client-widget.html`
- Backend API: `http://54.254.180.103:8000/docs`
- Rasa API: `http://54.254.180.103:5005`

**For detailed deployment instructions, see:**
- `deploy/DOCKER_DEPLOYMENT_GUIDE.md` - Complete AWS EC2 deployment guide
- `deploy/LOCAL_TESTING_GUIDE.md` - Local Docker testing instructions
- `deploy/README.md` - Deployment overview and quick reference

**Quick AWS EC2 Setup:**

1. **Upload project to EC2:**
   ```bash
   # From Windows machine
   cd deploy
   .\upload-to-ec2.bat
   ```

2. **Deploy on EC2:**
   ```bash
   # SSH to EC2 and run
   cd automotive_chatbot/deploy
   ./ec2-deploy.sh
   ```

3. **Access your application:**
   - Frontend: `http://your-ec2-ip:3000`
   - Backend API: `http://your-ec2-ip:8001/docs`
   - RASA API: `http://your-ec2-ip:5005`

**Management Commands (on EC2):**
```bash
./start-chatbot.sh    # Start platform
./stop-chatbot.sh     # Stop platform
./status-chatbot.sh   # Check status
./logs-chatbot.sh     # View logs
./update-chatbot.sh   # Update deployment
```

📖 **Detailed Guides:**
- [Complete AWS EC2 Deployment Guide](./deploy/AWS_EC2_DOCKER_DEPLOYMENT.md)
- [Docker Setup Guide](./deploy/DOCKER_SETUP_GUIDE.md)
- [Deployment README](./deploy/README.md)

### 🔧 Manual Deployment Alternatives

If the automated `upload-to-ec2.bat` script fails, use these manual alternatives:

**📋 Quick Reference:**
- [Manual Deployment Guide](./deploy/MANUAL_DEPLOYMENT_GUIDE.md) - Comprehensive manual methods
- [SFTP Instructions](./deploy/SFTP_INSTRUCTIONS.md) - Step-by-step SFTP upload
- [Alternative Methods](./deploy/ALTERNATIVE_DEPLOYMENT_METHODS.md) - GUI tools & cloud methods
- [Troubleshooting Guide](./deploy/TROUBLESHOOTING_GUIDE.md) - Common issues & solutions

**🚀 Quick Manual Upload:**
```powershell
# Windows PowerShell method
cd deploy
.\manual-scp-upload.ps1

# Windows Batch method
.\manual-scp-upload.bat
```

**🎯 Recommended for Windows Users:**
1. **WinSCP** (GUI) - User-friendly file transfer
2. **FileZilla** (GUI) - Cross-platform SFTP client
3. **Git-based** - Push to repository, clone on EC2
4. **VS Code Remote SSH** - Integrated development environment

**⚡ Emergency Methods:**
- AWS Systems Manager Session Manager (no SSH keys needed)
- Cloud storage transfer (S3, Google Drive, Dropbox)
- Docker Hub deployment
- Manual file creation via SSH

### Docker Troubleshooting

**Common Docker Issues:**
```bash
# Check container status
docker compose ps

# View specific service logs
docker compose logs backend
docker compose logs frontend
docker compose logs rasa

# Restart specific service
docker compose restart backend

# Clean rebuild
docker compose down
docker system prune -f
docker compose build --no-cache
docker compose up -d
```

**Memory Issues:**
- Ensure Docker has at least 8GB RAM allocated
- Close other applications if needed
- Use `docker stats` to monitor resource usage

**Port Conflicts:**
```bash
# Check port usage
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5005

# Kill conflicting processes
npm run kill-ports
```

### Installation & Setup

1. **Clone Repository**
```bash
git clone [repository-url]
cd automotive_chatbot
```

2. **Create Virtual Environment**
```bash
# Create and activate virtual environment
py -m venv .venv
.venv\Scripts\activate  # Windows Command Prompt
```

3. **Install All Dependencies**
```bash
# Run comprehensive setup (installs Python + Node.js dependencies)
python setup.py
```
*Expected time: 10-15 minutes for first install*

4. **Start All Services**
```bash
# Clean start (kills conflicting processes and starts all services)
npm run clean-start

# Alternative: Standard start
npm run dev:all
```

5. **Initial RASA Training**
```bash
# Train the RASA model
npm run rasa:train
```

## 🔄 Development Commands

### Service Management
```bash
npm run dev:all      # Start all services
npm run dev:core     # Start backend + frontend only
npm run clean-start  # Kill processes and fresh start
npm run kill-ports   # Kill conflicting processes
```

### RASA Training & Testing
```bash
npm run rasa:train          # Train RASA model
npm run rasa:test           # Test current model
npm run rasa:test-nlu       # Test NLU with cross-validation
npm run rasa:evaluate       # Full evaluation with metrics
npm run rasa:full-report    # Generate comprehensive report
```

### 🔄 COE Real-Time Monitor & Health Monitoring
Keep COE data automatically updated with smart LTA monitoring and health checks:

```bash
# Complete monitoring setup (recommended)
sudo ./deploy/setup_all_monitoring.sh

# Individual components
sudo ./deploy/aws_setup.sh                    # COE monitor only
./deploy/start_health_monitor.sh              # Health monitor only

# Manual startup
./start_coe_monitor.sh                        # COE monitor
./deploy/start_health_monitor.sh              # Health monitor

# Service management
sudo systemctl status coe-monitor chatbot-monitor
sudo journalctl -u coe-monitor -f
sudo journalctl -u chatbot-monitor -f
```

**AWS Deployment Options:**
- **EC2 with Systemd**: Reliable, cost-effective, always-on
- **ECS with Fargate**: Containerized, auto-scaling
- **Lambda with EventBridge**: Serverless, pay-per-use
- **Manual**: Direct monitoring for testing

See `docs/AWS_DEPLOYMENT_GUIDE.md` for detailed setup instructions.

## 🛠️ Project Structure

```
WireFrames/automotive_chatbot/
├── backend/
│   ├── api/
│   │   ├── external/       # RASA actions (modular)
│   │   │   ├── coe_actions.py
│   │   │   ├── loan_actions.py
│   │   │   ├── contact_actions.py
│   │   │   ├── vehicle_actions.py
│   │   │   └── feedback_actions.py
│   │   ├── boundaries/     # HTTP API layers
│   │   ├── controllers/    # Business logic
│   │   └── entities/       # Data models
│   ├── data/              # RASA training data
│   │   ├── nlu/           # Natural language understanding data
│   │   ├── stories/       # Conversation flows
│   │   └── rules/         # Rule-based responses (modular)
│   │       ├── basic_rules.yml      # Greetings & conversational
│   │       ├── fallback_rules.yml   # Error handling
│   │       ├── coe_rules.yml        # COE price queries
│   │       ├── vehicle_rules.yml    # Vehicle info & pricing
│   │       ├── service_rules.yml    # Test drives & maintenance
│   │       ├── support_rules.yml    # Contact & feedback
│   │       └── financial_rules.yml  # Loan calculations
│   ├── models/            # Trained RASA models
│   └── domain.yml         # RASA domain configuration
├── deploy/                 # AWS deployment scripts
│   ├── aws_setup.sh           # COE monitor setup
│   ├── setup_all_monitoring.sh # Complete monitoring setup
│   ├── start_monitoring.py    # Health monitoring system
│   ├── start_health_monitor.sh # Health monitor startup
│   ├── Dockerfile            # Container deployment
│   └── docker-compose.yml    # Local testing
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   └── components/    # React components
│   ├── public/            # Static files & widget
│   └── package.json       # Node.js dependencies
├── setup.py              # Automated setup script
└── quick-setup.md        # Detailed setup guide
```

## 🌐 Access Points

Once running, access these URLs:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main web interface |
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **RASA API** | http://localhost:5005 | RASA NLU/Core API |
| **RASA Actions** | http://localhost:5055 | Custom actions server |
| **Admin Dashboard** | http://localhost:3000/dashboard | Admin interface |

## 🎯 Widget Integration

### Embed Chatbot Widget
```html
<!-- Add to any website -->
<script src="http://YOUR_DOMAIN:3000/clevercompanion-widget.js"></script>
```

**For different environments:**
```html
<!-- Local Development -->
<script src="http://localhost:3000/clevercompanion-widget.js"></script>

<!-- Production (replace with your domain/IP) -->
<script src="http://your-domain.com:3000/clevercompanion-widget.js"></script>
<script src="http://54.123.45.67:3000/clevercompanion-widget.js"></script>
```

The widget automatically initializes and connects to the RASA backend using the unified domain configuration.

## 🔍 Troubleshooting

### Common Issues & Solutions

**Prerequisites Not Found:**
```bash
# Check installations
python --version  # or py --version
node --version
npm --version
```

**Port Conflicts:**
```bash
npm run kill-ports
npm run dev:all
```

**RASA Training Issues:**
```bash
# Check RASA installation
python -c "import rasa; print(rasa.__version__)"

# Force retrain model
cd backend
python -m rasa train --force
```

**Frontend Build Issues:**
```bash
cd frontend
npm install --force
npm run build
```

**Virtual Environment Issues:**
```bash
# Activate virtual environment
.venv\Scripts\activate  # Command Prompt (recommended)

# PowerShell (if execution policy allows)
.venv\Scripts\Activate.ps1
```

## 📞 Support & Documentation

### Getting Help
- **Setup Guide**: See `quick-setup.md` for detailed installation instructions
- **Architecture**: Review `ARCHITECTURE.md` for technical details
- **Technical Issues**: Check logs in respective service directories

### Important Notes
1. **RASA is mandatory** - Core requirement, cannot be removed
2. **Single requirements.txt** - Only one requirements file in `/backend/`
3. **Python 3.9.13** - Required for RASA 3.6.4 compatibility
4. **Node.js required** - Frontend will not work without Node.js/npm
5. **BCE backend only** - Frontend uses standard React patterns

---

## 🎉 Production Features

- ✅ **Error Handling**: Comprehensive error recovery and fallbacks
- ✅ **Responsive Design**: Mobile and desktop optimized
- ✅ **Performance**: Optimized API calls and caching
- ✅ **Security**: Input validation and sanitization
- ✅ **Monitoring**: Detailed logging and health checks
- ✅ **Scalability**: Modular architecture for easy expansion

**Latest Model**: RASA 3.6.4 trained with Singapore automotive data
**Status**: Production-ready with comprehensive testing
**Recent Update**: Rules modularized into functional categories for better maintainability

---

**Need detailed setup instructions?** See `quick-setup.md` for step-by-step installation guide.