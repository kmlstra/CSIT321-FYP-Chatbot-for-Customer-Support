import mongoose from 'mongoose';

const pricingSchema = new mongoose.Schema({
  planName: {
    type: String,
    required: true,
    trim: true
  },
  price: {
    type: Number,
    required: true
  },
  currency: {
    type: String,
    default: 'USD'
  },
  billingPeriod: {
    type: String,
    enum: ['monthly', 'yearly'],
    default: 'monthly'
  },
  features: [{
    type: String,
    trim: true
  }],
  isActive: {
    type: Boolean,
    default: true
  },
  isPopular: {
    type: Boolean,
    default: false
  }
}, {
  timestamps: true
});

export default mongoose.model('Pricing', pricingSchema);