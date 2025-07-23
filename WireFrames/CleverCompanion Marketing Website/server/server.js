import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/auth.js';
import testimonialRoutes from './routes/testimonials.js';
import faqRoutes from './routes/faqs.js';
import contactRoutes from './routes/contact.js';
import pricingRoutes from './routes/pricing.js';

// Temporarily hardcode environment variables
process.env.MONGODB_URI = 'mongodb+srv://darknesscrawler:P%40ssw0rd%211@marketing.agcqpdr.mongodb.net/marketing?retryWrites=true&w=majority&appName=Marketing';
process.env.JWT_SECRET = 'your-super-secret-jwt-key-here-make-it-long-and-random';
process.env.PORT = '3001';

// Debug: Check if environment variables are loaded
console.log('Environment check:');
console.log('MONGODB_URI exists:', !!process.env.MONGODB_URI);
console.log('JWT_SECRET exists:', !!process.env.JWT_SECRET);
console.log('PORT:', process.env.PORT);

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Connect to MongoDB
mongoose.connect(process.env.MONGODB_URI)
  .then(() => console.log('Connected to MongoDB'))
  .catch((error) => console.error('MongoDB connection error:', error));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/testimonials', testimonialRoutes);
app.use('/api/faqs', faqRoutes);
app.use('/api/contact', contactRoutes);
app.use('/api/pricing', pricingRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ message: 'Server is running!' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});