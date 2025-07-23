import mongoose from 'mongoose';

const testimonialSchema = new mongoose.Schema({
  quote: {
    type: String,
    required: true,
    trim: true
  },
  author: {
    type: String,
    required: true,
    trim: true
  },
  position: {
    type: String,
    required: true,
    trim: true
  },
  avatar: {
    type: String,
    default: 'https://randomuser.me/api/portraits/men/32.jpg'
  },
  rating: {
    type: Number,
    required: true,
    min: 1,
    max: 5,
    default: 5
  },
  isActive: {
    type: Boolean,
    default: true
  }
}, {
  timestamps: true
});

export default mongoose.model('Testimonial', testimonialSchema);