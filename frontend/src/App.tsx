import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './contexts/LanguageContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './pages/LandingPage';
import CatalogPage from './pages/CatalogPage';
import StudentPage from './pages/StudentPage';
import AdminPage from './pages/AdminPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <div className="min-h-screen flex flex-col bg-slate-50">
          <Navbar />
          <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/catalog" element={<CatalogPage />} />
              <Route path="/student" element={<StudentPage />} />
              <Route path="/admin" element={<AdminPage />} />
              {/* Catch-all: redirect unknown routes to landing */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </LanguageProvider>
    </BrowserRouter>
  );
};

export default App;
