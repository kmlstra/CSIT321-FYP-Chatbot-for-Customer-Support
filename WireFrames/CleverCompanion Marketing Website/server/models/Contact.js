import mongoose from 'mongoose';

const contactSchema = new mongoose.Schema({
  phone: {
    sales: { type: String, default: '(800) 123-4567' },
    support: { type: String, default: '(800) 765-4321' }
  },
  email: {
    sales: { type: String, default: 'sales@clevercompanion.com' },
    support: { type: String, default: 'support@clevercompanion.com' }
  },
  address: {
    street: { type: String, default: '123 Tech Boulevard, Suite 456' },
    city: { type: String, default: 'San Francisco' },
    state: { type: String, default: 'CA' },
    zip: { type: String, default: '94105' }
  },
  socialMedia: {
    facebook: { type: String, default: '#' },
    twitter: { type: String, default: '#' },
    linkedin: { type: String, default: '#' },
    instagram: { type: String, default: '#' }
  }
}, {
  timestamps: true
});

export default mongoose.model('Contact', contactSchema);