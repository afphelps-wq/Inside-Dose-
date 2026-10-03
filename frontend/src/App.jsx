import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Home from './pages/Home.jsx'
import Drug from './pages/Drug.jsx'
import MyDrugs from './pages/MyDrugs.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/drug/:rxcui" element={<Drug />} />
        <Route path="/my-drugs" element={<MyDrugs />} />
      </Route>
    </Routes>
  )
}
