import { useState } from 'react'
import Layout from './components/Layout'
import JobList from './pages/JobList'
import EmployeeList from './pages/EmployeeList'
import EquipmentList from './pages/EquipmentList'
import './App.css'

function App() {
  const [tab, setTab] = useState('jobs')

  return (
    <Layout tab={tab} setTab={setTab}>
      {tab === 'jobs' && <JobList />}
      {tab === 'employees' && <EmployeeList />}
      {tab === 'equipment' && <EquipmentList />}
    </Layout>
  )
}

export default App
