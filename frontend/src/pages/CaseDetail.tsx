/**
 * Case Detail Page - Phronesis LEX
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { casesApi, contradictionsApi } from '../services/api';

export function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: caseData, isLoading: caseLoading } = useQuery({
    queryKey: ['case', id],
    queryFn: () => casesApi.get(id!),
    enabled: !!id,
  });

  const { data: stats } = useQuery({
    queryKey: ['case-stats', id],
    queryFn: () => casesApi.getStats(id!),
    enabled: !!id,
  });

  const detectMutation = useMutation({
    mutationFn: () => contradictionsApi.detect(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-stats', id] });
      queryClient.invalidateQueries({ queryKey: ['case', id] });
    },
  });

  if (caseLoading || !caseData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{caseData.reference}</h1>
            <span className={`badge ${
              caseData.status === 'active' ? 'status-active' : 
              caseData.status === 'pending' ? 'status-pending' : 
              'status-completed'
            }`}>
              {caseData.status}
            </span>
          </div>
          <p className="text-slate-400 mt-1">{caseData.title || 'Untitled'}</p>
          <div className="flex gap-4 mt-2 text-sm text-slate-500">
            <span>{caseData.case_type_display}</span>
            {caseData.court && <span>• {caseData.court}</span>}
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => detectMutation.mutate()}
            disabled={detectMutation.isPending}
            className="btn-primary flex items-center gap-2"
          >
            {detectMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Detecting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Detect Contradictions
              </>
            )}
          </button>
        </div>
      </div>

      {/* Key Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {[
          { label: 'Documents', value: stats?.documents || 0, link: `/cases/${id}/documents` },
          { label: 'Claims', value: stats?.claims || 0, link: `/cases/${id}/claims` },
          { label: 'Contradictions', value: stats?.contradictions || 0, link: `/cases/${id}/contradictions`, highlight: true },
          { label: 'Bias Signals', value: stats?.bias_indicators || 0, link: `/cases/${id}/bias` },
          { label: 'Timeline Events', value: stats?.timeline_events || 0, link: `/cases/${id}/timeline` },
          { label: 'Entities', value: stats?.entities || 0 },
          { label: 'Arguments', value: stats?.arguments || 0, link: `/cases/${id}/arguments` },
        ].map((stat, i) => (
          <Link
            key={stat.label}
            to={stat.link || '#'}
            className={`card p-4 text-center card-hover ${stat.highlight && (stat.value as number) > 0 ? 'border-red-500/30' : ''}`}
          >
            <p className={`text-2xl font-bold ${stat.highlight && (stat.value as number) > 0 ? 'text-red-400' : 'text-white'}`}>
              {stat.value}
            </p>
            <p className="text-xs text-slate-500 mt-1">{stat.label}</p>
          </Link>
        ))}
      </div>

      {/* Analysis Summary */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Claims by Type */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Claims by Type</h3>
            <div className="space-y-3">
              {stats.claims_by_type && Object.entries(stats.claims_by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-slate-400 capitalize">{type.replace('_', ' ')}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(count / (stats.claims || 1)) * 100}%` }}
                      />
                    </div>
                    <span className="text-white w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
              {!stats.claims_by_type || Object.keys(stats.claims_by_type).length === 0 && (
                <p className="text-slate-500 text-center py-4">No claims extracted yet</p>
              )}
            </div>
          </div>

          {/* Contradictions Summary */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Contradiction Analysis</h3>
            {stats.contradictions > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-red-400">{stats.self_contradictions}</p>
                    <p className="text-xs text-slate-500">Self-Contradictions</p>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg text-center">
                    <p className="text-2xl font-bold text-amber-400">{stats.unresolved_contradictions}</p>
                    <p className="text-xs text-slate-500">Unresolved</p>
                  </div>
                </div>
                {stats.contradictions_by_severity && (
                  <div className="space-y-2">
                    {Object.entries(stats.contradictions_by_severity).map(([sev, count]) => (
                      <div key={sev} className="flex items-center justify-between">
                        <span className={`badge badge-${sev}`}>{sev}</span>
                        <span className="text-white">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-slate-500 mb-4">No contradictions detected yet</p>
                <button
                  onClick={() => detectMutation.mutate()}
                  disabled={detectMutation.isPending || (stats.claims || 0) < 2}
                  className="btn-secondary"
                >
                  {(stats.claims || 0) < 2 ? 'Need at least 2 claims' : 'Run Detection'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Navigation */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Analysis Tools</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Documents', desc: 'Upload and manage documents', link: `/cases/${id}/documents`, icon: '📄' },
            { label: 'Claims', desc: 'View extracted claims', link: `/cases/${id}/claims`, icon: '💬' },
            { label: 'Contradictions', desc: 'Review contradictions', link: `/cases/${id}/contradictions`, icon: '⚠️' },
            { label: 'Bias Analysis', desc: 'Statistical bias detection', link: `/cases/${id}/bias`, icon: '⚖️' },
            { label: 'Timeline', desc: 'Chronological events', link: `/cases/${id}/timeline`, icon: '📅' },
            { label: 'Arguments', desc: 'Toulmin arguments', link: `/cases/${id}/arguments`, icon: '📋' },
          ].map((item) => (
            <Link
              key={item.label}
              to={item.link}
              className="p-4 bg-slate-800/50 rounded-lg hover:bg-slate-700/50 transition-colors"
            >
              <span className="text-2xl mb-2 block">{item.icon}</span>
              <p className="font-medium text-white">{item.label}</p>
              <p className="text-xs text-slate-500 mt-1">{item.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

