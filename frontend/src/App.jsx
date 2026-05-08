import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import InputPage from './pages/InputPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import DetailPage from './pages/DetailPage.jsx'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/"               element={<InputPage />} />
        <Route path="/results"        element={<ResultsPage />} />
        <Route path="/stocks/:ticker" element={<DetailPage />} />
      </Routes>
    </Layout>
  )
}
