import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import HeroBanner from './components/HeroBanner';
import FeaturedVehicles from './components/FeaturedVehicles';
import ExternalChatBot from './components/ChatBot.tsx';
import Footer from './components/Footer';
import SearchPage from './pages/SearchPage';
import VehicleDetails from './pages/VehicleDetails';
import FinancialPlanner from './pages/FinancialPlanner';
import FAQ from './pages/FAQ';
import Contact from './pages/Contact';
import Profile from './pages/Profile';
import UserDashboard from './pages/UserDashboard';
import Login from './components/Login';
import Register from './components/Register';
import AdminDashboard from './components/AdminDashboard';

function App() {
  return (
      <Router>
        <div className="min-h-screen flex flex-col">
          <Header />
          <Routes>
            <Route path="/" element={
              <main className="flex-grow">
                <HeroBanner />
                <FeaturedVehicles />
              </main>
            } />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/vehicle/:id" element={<VehicleDetails />} />
            <Route path="/finance" element={<FinancialPlanner />} />
            <Route path="/faq" element={<FAQ />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/dashboard" element={<UserDashboard />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
          <ExternalChatBot />
          <Footer />
        </div>
      </Router>
  );
}

export default App;