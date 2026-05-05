import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/layouts/Layout'
import { Loading } from './components/common'

// Lazy-load all pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Publications = lazy(() => import('./pages/Publications'))
const PublicationDetail = lazy(() => import('./pages/PublicationDetail'))
const Authors = lazy(() => import('./pages/Authors'))
const AuthorProfile = lazy(() => import('./pages/AuthorProfile'))
const Search = lazy(() => import('./pages/Search'))
const Analytics = lazy(() => import('./pages/Analytics'))
const TeamBuilder = lazy(() => import('./pages/TeamBuilder'))
const RAGAnalysis = lazy(() => import('./pages/RAGAnalysis'))
const FacultyEvaluation = lazy(() => import('./pages/FacultyEvaluation'))

function App() {
  return (
    <Suspense fallback={<Loading message="Loading..." />}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="publications" element={<Publications />} />
          <Route path="publications/:id" element={<PublicationDetail />} />
          <Route path="authors" element={<Authors />} />
          <Route path="authors/:id" element={<AuthorProfile />} />
          <Route path="faculty/:id/evaluation" element={<FacultyEvaluation />} />
          <Route path="search" element={<Search />} />
          <Route path="teams" element={<TeamBuilder />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="rag" element={<RAGAnalysis />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default App
