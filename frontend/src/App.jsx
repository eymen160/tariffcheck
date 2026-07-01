import { Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ResultsPage from './pages/ResultsPage'
import CapePage from './pages/CapePage'
import LookupPage from './pages/LookupPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/results" element={<ResultsPage />} />
      <Route path="/cape-refund" element={<CapePage />} />
      <Route path="/hts-lookup" element={<LookupPage />} />
    </Routes>
  )
}
