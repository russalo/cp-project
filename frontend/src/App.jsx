import { useState } from 'react'
import Layout from './components/Layout'
import EmployeeList from './pages/EmployeeList'
import EquipmentList from './pages/EquipmentList'
import './App.css'

function App() {
  const [tab, setTab] = useState('employees')

  return (
    <Layout tab={tab} setTab={setTab}>
      {tab === 'employees' ? <EmployeeList /> : <EquipmentList />}
    </Layout>
  )
}

export default App
