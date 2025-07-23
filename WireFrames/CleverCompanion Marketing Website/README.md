# CleverCompanion - AI ChatBot for Car Dealerships

CleverCompanion is a comprehensive AI-powered chatbot solution designed specifically for car dealerships. It features a modern React frontend with a Node.js/Express backend, MongoDB database, and a complete admin dashboard for content management.

## 🚀 Features

- **AI-Powered Chatbot Interface** - Interactive chat simulation for car dealership customers
- **Admin Dashboard** - Complete content management system
- **Dynamic Content Management** - Testimonials, FAQs, Pricing, and Contact information
- **User Authentication** - Secure admin login system
- **Responsive Design** - Works perfectly on desktop and mobile devices
- **Real-time Data** - All content is dynamically loaded from MongoDB

## 🛠 Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Lucide React** for icons

### Backend
- **Node.js** with Express
- **MongoDB** with Mongoose ODM
- **JWT** for authentication
- **bcryptjs** for password hashing
- **CORS** enabled for cross-origin requests

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (version 16 or higher)
- **npm** (comes with Node.js)
- **MongoDB Atlas account** (or local MongoDB installation)
- **Git** (for cloning the repository)

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd Marketing
```

### 2. Install Dependencies
```bash
# Install frontend dependencies
npm install

# Install backend dependencies (if needed)
cd server
npm install
cd ..
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
VITE_API_URL=http://localhost:3001
```

### 4. Database Setup
The project uses MongoDB Atlas. The connection is already configured in `server/server.js`:
- **Database**: MongoDB Atlas
- **Connection**: Pre-configured with credentials
- **Collections**: users, testimonials, faqs, contacts, pricings

### 5. Populate Database (Optional)
If you want to populate the database with sample data:
```bash
python populate_db.py
```

### 6. Start the Application
```bash
# Start both frontend and backend servers
npm run dev:full
```

This will start:
- **Backend server** on `http://localhost:3001`
- **Frontend server** on `http://localhost:5173`

## 🔑 Default Credentials

### Admin Access
- **URL**: `http://localhost:5173/admin/login`
- **Email**: `admin@clevercompanion.com`
- **Password**: `admin123`

### Database Credentials
- **MongoDB URI**: Pre-configured in server
- **Database Name**: `marketing`
- **Username**: `darknesscrawler`
- **Password**: `P@ssw0rd!1`

## 📱 Usage

### For End Users
1. **Homepage** (`/`) - Main landing page with hero section and features
2. **Features** (`/features`) - Detailed feature descriptions
3. **Pricing** (`/pricing`) - Dynamic pricing information
4. **FAQ** (`/faq`) - Frequently asked questions with search
5. **Testimonials** (`/testimonials`) - Customer success stories
6. **Contact** (`/contact`) - Contact information and form

### For Administrators
1. **Login** at `/admin/login` with the credentials above
2. **Dashboard** (`/admin`) - Access to content management:
   - **Testimonials Management** - Add, edit, delete customer testimonials
   - **FAQ Management** - Manage frequently asked questions by category
   - **Contact Information** - Update phone, email, address, and social media
   - **Pricing Management** - Manage pricing plans and features

## 🗂 Project Structure

```
Marketing/
├── src/                          # Frontend source code
│   ├── components/              # Reusable React components
│   │   ├── Header.tsx          # Navigation header
│   │   ├── Footer.tsx          # Site footer
│   │   ├── Hero.tsx            # Hero section with chatbot demo
│   │   ├── Features.tsx        # Features showcase
│   │   ├── Testimonials.tsx    # Testimonials section
│   │   └── Cta.tsx            # Call-to-action section
│   ├── pages/                  # Page components
│   │   ├── HomePage.tsx        # Main landing page
│   │   ├── FeaturesPage.tsx    # Features page
│   │   ├── PricingPage.tsx     # Pricing page
│   │   ├── FaqPage.tsx         # FAQ page
│   │   ├── TestimonialsPage.tsx # Testimonials page
│   │   ├── ContactPage.tsx     # Contact page
│   │   ├── AdminPage.tsx       # Admin dashboard
│   │   └── AdminLoginPage.tsx  # Admin login
│   ├── contexts/               # React contexts
│   │   └── AuthContext.tsx     # Authentication context
│   ├── hooks/                  # Custom React hooks
│   │   └── useApi.ts          # API interaction hook
│   └── img/                    # Images and assets
├── server/                     # Backend source code
│   ├── models/                 # MongoDB models
│   │   ├── User.js            # User model
│   │   ├── Testimonial.js     # Testimonial model
│   │   ├── FAQ.js             # FAQ model
│   │   ├── Contact.js         # Contact model
│   │   └── Pricing.js         # Pricing model
│   ├── routes/                 # API routes
│   │   ├── auth.js            # Authentication routes
│   │   ├── testimonials.js    # Testimonials CRUD
│   │   ├── faqs.js            # FAQs CRUD
│   │   ├── contact.js         # Contact management
│   │   └── pricing.js         # Pricing management
│   ├── middleware/             # Express middleware
│   │   └── auth.js            # Authentication middleware
│   └── server.js              # Main server file
├── populate_db.py             # Database population script
├── package.json               # Dependencies and scripts
└── README.md                  # This file
```

## 🔧 Available Scripts

```bash
# Development
npm run dev              # Start frontend only
npm run server          # Start backend only
npm run dev:full        # Start both frontend and backend

# Production
npm run build           # Build for production
npm run preview         # Preview production build

# Linting
npm run lint            # Run ESLint
```

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user

### Testimonials
- `GET /api/testimonials` - Get active testimonials
- `GET /api/testimonials/admin` - Get all testimonials (admin)
- `POST /api/testimonials` - Create testimonial (admin)
- `PUT /api/testimonials/:id` - Update testimonial (admin)
- `DELETE /api/testimonials/:id` - Delete testimonial (admin)

### FAQs
- `GET /api/faqs` - Get active FAQs
- `GET /api/faqs/admin` - Get all FAQs (admin)
- `POST /api/faqs` - Create FAQ (admin)
- `PUT /api/faqs/:id` - Update FAQ (admin)
- `DELETE /api/faqs/:id` - Delete FAQ (admin)

### Contact
- `GET /api/contact` - Get contact information
- `PUT /api/contact` - Update contact information (admin)

### Pricing
- `GET /api/pricing` - Get active pricing plans
- `GET /api/pricing/admin` - Get all pricing plans (admin)
- `POST /api/pricing` - Create pricing plan (admin)
- `PUT /api/pricing/:id` - Update pricing plan (admin)
- `DELETE /api/pricing/:id` - Delete pricing plan (admin)

## 🔒 Security Features

- **JWT Authentication** - Secure token-based authentication
- **Password Hashing** - bcryptjs for secure password storage
- **Role-based Access** - Admin-only routes and functionality
- **CORS Configuration** - Proper cross-origin resource sharing
- **Input Validation** - Server-side validation for all inputs

## 🚀 Deployment

### Frontend Deployment
The frontend can be deployed to any static hosting service:
1. Run `npm run build`
2. Deploy the `dist` folder to your hosting service
3. Update the `VITE_API_URL` environment variable

### Backend Deployment
The backend can be deployed to services like Heroku, Railway, or DigitalOcean:
1. Ensure MongoDB connection string is configured
2. Set environment variables for production
3. Deploy the `server` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- **Email**: admin@clevercompanion.com
- **Phone**: (800) 123-4567

## 🔄 Version History

- **v1.0.0** - Initial release with full functionality
  - AI chatbot interface
  - Admin dashboard
  - Dynamic content management
  - User authentication
  - Responsive design

---

**Built with ❤️ for modern car dealerships**