import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Sidebar, PageContainer } from './components/layout/Sidebar'
import HomePage from './pages/HomePage'
import UploadPage from './pages/UploadPage'
import DashboardPage from './pages/DashboardPage'
import ReportPage from './pages/ReportPage'
import PolicyPage from './pages/PolicyPage'

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-slate-950 text-slate-50">
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      <PageContainer onMenuClick={() => setIsSidebarOpen(true)}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/analysis/:jobId" element={<DashboardPage />} />
          <Route path="/report" element={<ReportPage />} />
          <Route path="/report/:jobId" element={<ReportPage />} />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="/policy/:jobId" element={<PolicyPage />} />
        </Routes>
      </PageContainer>
    </div>
  )
}

export default App
