import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { casesApi, analysisApi } from '../services/api';
import { useState } from 'react';
import RunAnalysisButton from '../components/RunAnalysisButton';

export default function CaseDetail() {
  const { caseId } = useParams();
  const queryClient = useQueryClient();
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Fetch Case Data
  const { data: activeCase, isLoading: caseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => casesApi.get(caseId),
  });

  // Fetch Case Stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['caseStats', caseId],
    queryFn: () => casesApi.getStats(caseId),
    enabled: !!caseId,
    refetchInterval: isAnalyzing ? 2000 : 30000, // Poll more frequently if analyzing
  });

  // Check for active analysis runs
  const { data: runs } = useQuery({
    queryKey: ['analysisRuns', caseId],
    queryFn: () => analysisApi.list(caseId),
    enabled: !!caseId,
    onSuccess: (data) => {
        const active = data.results?.find(r => r.status === 'running' || r.status === 'pending');
        setIsAnalyzing(!!active);
    }
  });

  // Analysis Mutation
  const analyzeMutation = useMutation({
    mutationFn: () => casesApi.analyze(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries(['analysisRuns', caseId]);
      setIsAnalyzing(true);
    },
  });

  if (caseLoading) return <div className="p-8 text-center text-gray-500 font-mono">Loading case details...</div>;
  if (caseError) return <div className="p-8 text-center text-accent-red font-mono">Error: {caseError.message}</div>;
  if (!activeCase) return <div className="p-8 text-center text-gray-500 font-mono">Case not found</div>;

  const safeStats = stats || {
    documents: 0,
    claims: 0,
    timeline_events: 0,
    bias_indicators: 0,
    contradictions: 0
  };

  return (
    <div className="fade-in">
      {/* Header Section */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link to="/" className="text-xs font-mono text-gray-500 hover:text-accent-brass mb-2 flex items-center gap-1 w-fit">
            <span className="material-symbols-outlined text-sm">arrow_back</span>
            Back to Dashboard
          </Link>
          <h1 className="text-3xl font-display font-bold text-white tracking-wide mb-1">Investigation Command</h1>
          <p className="text-xs font-mono text-gray-400">
            Case Reference: <span className="text-accent-brass">{activeCase.reference}</span> ·
            Subject: <span className="text-white">{activeCase.subject || 'Unknown'}</span>
          </p>
        </div>
        <div className="flex gap-3">
            {/* Run Analysis Button */}
            <RunAnalysisButton caseId={caseId} />
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Documents Metric */}
        <div className="group bg-dark-800 rounded-xl p-5 border border-dark-700 hover:border-accent-brass/50 transition cursor-pointer relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                <span className="material-symbols-outlined text-6xl">description</span>
            </div>
            <div className="relative z-10">
                <div className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1">Documents</div>
                <div className="text-3xl font-bold text-white mb-2">{safeStats.documents}</div>
                <div className="w-full bg-dark-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-gray-400 h-full" style={{ width: '100%' }}></div>
                </div>
            </div>
        </div>

        {/* Claims Metric */}
        <div className="group bg-dark-800 rounded-xl p-5 border border-dark-700 hover:border-accent-copper/50 transition cursor-pointer relative overflow-hidden">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                <span className="material-symbols-outlined text-6xl">hub</span>
            </div>
            <div className="relative z-10">
                <div className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1">Claims Extracted</div>
                <div className="text-3xl font-bold text-accent-copper mb-2">{safeStats.claims}</div>
                 <div className="w-full bg-dark-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-accent-copper h-full" style={{ width: '75%' }}></div>
                </div>
            </div>
        </div>

        {/* Biases Metric */}
        <div className="group bg-dark-800 rounded-xl p-5 border border-dark-700 hover:border-accent-red/50 transition cursor-pointer relative overflow-hidden">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                <span className="material-symbols-outlined text-6xl">warning</span>
            </div>
            <div className="relative z-10">
                <div className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1">Bias Indicators</div>
                <div className="text-3xl font-bold text-accent-red mb-2">{safeStats.bias_indicators}</div>
                 <div className="w-full bg-dark-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-accent-red h-full" style={{ width: '40%' }}></div>
                </div>
            </div>
        </div>
        
        {/* Timeline Metric */}
        <div className="group bg-dark-800 rounded-xl p-5 border border-dark-700 hover:border-accent-green/50 transition cursor-pointer relative overflow-hidden">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition">
                <span className="material-symbols-outlined text-6xl">schedule</span>
            </div>
            <div className="relative z-10">
                <div className="text-[10px] font-mono text-gray-500 uppercase tracking-widest mb-1">Timeline Events</div>
                <div className="text-3xl font-bold text-accent-green mb-2">{safeStats.timeline_events}</div>
                 <div className="w-full bg-dark-700 h-1 rounded-full overflow-hidden">
                    <div className="bg-accent-green h-full" style={{ width: '60%' }}></div>
                </div>
            </div>
        </div>
      </div>

      {/* Analysis Status Bar */}
      {isAnalyzing && (
          <div className="mb-8 bg-dark-800 border border-accent-brass/30 rounded-xl p-4 animate-pulse">
              <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-accent-brass uppercase font-bold flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-accent-brass animate-ping"></span>
                      Analysis in Progress
                  </span>
                  <span className="text-xs text-gray-400">Processing documents...</span>
              </div>
              <div className="w-full bg-dark-700 h-2 rounded-full overflow-hidden">
                  <div className="bg-accent-brass h-full animate-progress-indeterminate"></div>
              </div>
          </div>
      )}

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity / Documents */}
        <div className="lg:col-span-2 space-y-6">
            {/* Add more detailed views here later */}
            <div className="bg-dark-800 rounded-xl border border-dark-700 p-8 text-center">
                <div className="text-gray-500 font-mono mb-2">Detailed views available after analysis</div>
                <div className="flex justify-center gap-4 mt-4">
                    <Link to="documents" className="px-4 py-2 bg-dark-700 rounded hover:bg-dark-600 text-sm text-white">Documents</Link>
                    <Link to="claims" className="px-4 py-2 bg-dark-700 rounded hover:bg-dark-600 text-sm text-white">Claims</Link>
                    <Link to="timeline" className="px-4 py-2 bg-dark-700 rounded hover:bg-dark-600 text-sm text-white">Timeline</Link>
                </div>
            </div>
        </div>

        {/* Sidebar Widgets */}
        <div className="space-y-6">
            {/* System Status */}
            <div className="bg-dark-800 rounded-xl border border-dark-700 p-4">
                <h3 className="font-mono text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">System Status</h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-400">Backend Connection</span>
                        <span className="flex items-center gap-1.5 text-[10px] font-mono text-accent-green">
                            <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse"></span>
                            ONLINE
                        </span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-400">AI Reasoning</span>
                        <span className={`flex items-center gap-1.5 text-[10px] font-mono ${isAnalyzing ? 'text-accent-brass' : 'text-gray-500'}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${isAnalyzing ? 'bg-accent-brass animate-ping' : 'bg-gray-500'}`}></span>
                            {isAnalyzing ? 'PROCESSING' : 'IDLE'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
