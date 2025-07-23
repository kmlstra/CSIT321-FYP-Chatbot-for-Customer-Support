import express from 'express';
import Pricing from '../models/Pricing.js';
import { adminAuth } from '../middleware/auth.js';

const router = express.Router();

// Get all active pricing plans
router.get('/', async (req, res) => {
  try {
    const pricing = await Pricing.find({ isActive: true })
      .sort({ price: 1 });
    res.json(pricing);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Get all pricing plans (admin only)
router.get('/admin', adminAuth, async (req, res) => {
  try {
    const pricing = await Pricing.find()
      .sort({ price: 1 });
    res.json(pricing);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Create pricing plan (admin only)
router.post('/', adminAuth, async (req, res) => {
  try {
    const pricing = new Pricing(req.body);
    await pricing.save();
    res.status(201).json(pricing);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Update pricing plan (admin only)
router.put('/:id', adminAuth, async (req, res) => {
  try {
    const pricing = await Pricing.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true }
    );
    if (!pricing) {
      return res.status(404).json({ message: 'Pricing plan not found' });
    }
    res.json(pricing);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Delete pricing plan (admin only)
router.delete('/:id', adminAuth, async (req, res) => {
  try {
    const pricing = await Pricing.findByIdAndDelete(req.params.id);
    if (!pricing) {
      return res.status(404).json({ message: 'Pricing plan not found' });
    }
    res.json({ message: 'Pricing plan deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

export default router;