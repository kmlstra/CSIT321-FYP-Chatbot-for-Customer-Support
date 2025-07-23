import express from 'express';
import FAQ from '../models/FAQ.js';
import { adminAuth } from '../middleware/auth.js';

const router = express.Router();

// Get all active FAQs
router.get('/', async (req, res) => {
  try {
    const faqs = await FAQ.find({ isActive: true })
      .sort({ category: 1, order: 1 });
    res.json(faqs);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Get all FAQs (admin only)
router.get('/admin', adminAuth, async (req, res) => {
  try {
    const faqs = await FAQ.find()
      .sort({ category: 1, order: 1 });
    res.json(faqs);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Create FAQ (admin only)
router.post('/', adminAuth, async (req, res) => {
  try {
    const faq = new FAQ(req.body);
    await faq.save();
    res.status(201).json(faq);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Update FAQ (admin only)
router.put('/:id', adminAuth, async (req, res) => {
  try {
    const faq = await FAQ.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true }
    );
    if (!faq) {
      return res.status(404).json({ message: 'FAQ not found' });
    }
    res.json(faq);
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

// Delete FAQ (admin only)
router.delete('/:id', adminAuth, async (req, res) => {
  try {
    const faq = await FAQ.findByIdAndDelete(req.params.id);
    if (!faq) {
      return res.status(404).json({ message: 'FAQ not found' });
    }
    res.json({ message: 'FAQ deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Server error', error: error.message });
  }
});

export default router;