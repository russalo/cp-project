import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import JobList from './pages/JobList'
import JobDetail from './pages/JobDetail'
import EmployeeList from './pages/EmployeeList'
import EquipmentList from './pages/EquipmentList'
import EwoDetail from './pages/EwoDetail'
import EwoNew from './pages/EwoNew'
import EwoPrint from './pages/EwoPrint'
import WorkDayDetail from './pages/WorkDayDetail'
import WorkDayNew from './pages/WorkDayNew'
import './App.css'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/jobs" replace />} />
        <Route path="/jobs" element={<JobList />} />
        <Route path="/jobs/:jobId" element={<JobDetail />} />
        <Route path="/jobs/:jobId/ewos/new" element={<EwoNew />} />
        <Route path="/ewos/:ewoId" element={<EwoDetail />} />
        <Route path="/ewos/:ewoId/print" element={<EwoPrint />} />
        <Route path="/ewos/:ewoId/workdays/new" element={<WorkDayNew />} />
        <Route path="/workdays/:workDayId" element={<WorkDayDetail />} />
        <Route path="/employees" element={<EmployeeList />} />
        <Route path="/equipment" element={<EquipmentList />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  )
}

function NotFound() {
  return (
    <div className="page">
      <h1 className="page-title">Not found</h1>
      <p>The page you’re looking for doesn’t exist.</p>
    </div>
  )
}
