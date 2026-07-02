import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import CapePage from './pages/CapePage'
import LookupPage from './pages/LookupPage'
import BatchPage from './pages/BatchPage'
import CalculatorPage from './pages/CalculatorPage'
import SavingsPage from './pages/SavingsPage'
import BrokersPage from './pages/BrokersPage'
import PricingPage from './pages/PricingPage'
import TermsPage from './pages/TermsPage'
import NotFoundPage from './pages/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/results" element={<ResultsPage />} />
      <Route path="/cape-refund" element={<CapePage />} />
      <Route path="/hts-lookup" element={<LookupPage />} />
      <Route path="/batch" element={<BatchPage />} />
      <Route path="/calculator" element={<CalculatorPage />} />
      <Route path="/savings" element={<SavingsPage />} />
      <Route path="/brokers" element={<BrokersPage />} />
      <Route path="/pricing" element={<PricingPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
