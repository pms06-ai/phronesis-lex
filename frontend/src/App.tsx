/**
 * Phronesis LEX - Forensic Case Intelligence Platform
 * Main Application Component
 */
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { CaseList } from './pages/CaseList';
import { CaseDetail } from './pages/CaseDetail';
import { Documents } from './pages/Documents';
import { Claims } from './pages/Claims';
import { Contradictions } from './pages/Contradictions';
import { BiasAnalysis } from './pages/BiasAnalysis';
import { Timeline } from './pages/Timeline';
import { Arguments } from './pages/Arguments';
import { LegalRules } from './pages/LegalRules';
import AIWorkflow from './pages/AIWorkflow';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cases" element={<CaseList />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/cases/:id/documents" element={<Documents />} />
            <Route path="/cases/:id/claims" element={<Claims />} />
            <Route path="/cases/:id/contradictions" element={<Contradictions />} />
            <Route path="/cases/:id/bias" element={<BiasAnalysis />} />
            <Route path="/cases/:id/timeline" element={<Timeline />} />
            <Route path="/cases/:id/arguments" element={<Arguments />} />
            <Route path="/cases/:caseId/ai-workflow" element={<AIWorkflow />} />
            <Route path="/legal-rules" element={<LegalRules />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;

