# EZ Autos - Car Dealership Platform

A full-stack web application for car dealership management with React frontend and Django backend.

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v16 or higher) - [Download here](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download here](https://python.org/)
- **Git** - [Download here](https://git-scm.com/)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd ez-autos
```

### 2. Backend Setup (Django)

#### Install Python Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Database Setup
```bash
# Run database migrations
python manage.py migrate

# Create admin user (optional - one already exists)
python manage.py ensure_admin
```

#### Start Backend Server
```bash
python manage.py runserver
```
The backend will be available at `http://localhost:8000`

### 3. Frontend Setup (React)

Open a new terminal window/tab:

```bash
# Install Node.js dependencies
npm install

# Start development server
npm run dev
```
The frontend will be available at `http://localhost:5173`

## 🔧 Environment Configuration

### Backend Environment Variables

Create a `.env` file in the root directory (if not already present):

```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
MONGODB_URI=your-mongodb-connection-string
MONGODB_NAME=ezautos
```

### Frontend Environment Variables

The frontend uses Vite environment variables. Update `src/lib/api.ts` if your backend runs on a different port.

## 👤 Default Admin Credentials

- **Email:** admin@example.com
- **Password:** admin

## 📁 Project Structure

```
ez-autos/
├── backend/                 # Django backend
│   ├── settings.py         # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── api/                    # Django API app
│   ├── models.py          # Database models
│   ├── views.py           # API endpoints
│   ├── urls.py            # API URL routing
│   └── serializers.py     # Data serializers
├── src/                    # React frontend
│   ├── components/        # React components
│   ├── pages/            # Page components
│   ├── lib/              # Utilities and API client
│   └── types/            # TypeScript type definitions
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
└── README.md             # This file
```

## 🛠 Development Commands

### Backend Commands
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test
```

### Frontend Commands
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout
- `GET /api/profile/` - Get user profile

### Admin Endpoints (Requires admin role)
- `GET /api/knowledge-base/` - Get knowledge base articles
- `POST /api/knowledge-base/` - Create knowledge base article
- `GET /api/test-drives/` - Get test drive bookings
- `GET /api/chat-history/` - Get chat history
- `GET /api/feedback/` - Get user feedback
- `GET /api/team-members/` - Get team members

## 🔒 Authentication & Authorization

The application uses Django's session-based authentication:
- Users can register and login
- Admin users have access to the admin dashboard
- Regular users can browse vehicles and use the chatbot

## 🎨 Frontend Features

- **Responsive Design** - Works on desktop, tablet, and mobile
- **Vehicle Search** - Advanced search and filtering
- **Financial Planner** - Loan calculator
- **Chatbot** - Customer support chat
- **Admin Dashboard** - Management interface for admins

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Backend (Django)
   python manage.py runserver 8001
   
   # Frontend (Vite)
   npm run dev -- --port 5174
   ```

2. **Database connection issues**
   - Ensure MongoDB is running (if using MongoDB features)
   - Check your `.env` file configuration

3. **CORS issues**
   - The backend is configured to allow requests from `localhost:5173`
   - Update `CORS_ALLOWED_ORIGINS` in `backend/settings.py` if needed

4. **Module not found errors**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   npm install
   ```

## 🚀 Production Deployment

### Backend (Django)
1. Set `DEBUG=False` in production
2. Configure proper database (PostgreSQL recommended)
3. Set up static file serving
4. Use a production WSGI server like Gunicorn

### Frontend (React)
1. Build the application: `npm run build`
2. Serve the `dist` folder using a web server
3. Configure environment variables for production API URL

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Commit your changes: `git commit -m 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Look for existing issues in the repository
3. Create a new issue with detailed information about the problem

---

**Happy coding! 🚗💨**