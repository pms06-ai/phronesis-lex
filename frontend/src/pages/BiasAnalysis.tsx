/**
 * Bias Analysis Page - Phronesis LEX
 */
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { biasApi } from '../services/api';

export function BiasAnalysis() {
  const { id: caseId } = useParams<{ id: string }>();

  const { data: report, isLoading } = useQuery({
    queryKey: ['bias-report', caseId],
    queryFn: () => biasApi.getReport(caseId!),
    enabled: !!caseId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Bias Analysis</h1>
        <p className="text-slate-400 mt-1">
          Statistical analysis of linguistic patterns against corpus baselines
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-white">{report?.total_signals || 0}</p>
          <p className="text-xs text-slate-500">Total Signals</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-red-400">
            {report?.statistical_summary?.signals_above_critical || 0}
          </p>
          <p className="text-xs text-slate-500">Critical (|z|≥2)</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-amber-400">
            {report?.statistical_summary?.signals_above_warning || 0}
          </p>
          <p className="text-xs text-slate-500">Warning (|z|≥1.5)</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-white">
            {report?.statistical_summary?.mean_z_score?.toFixed(2) || '—'}
          </p>
          <p className="text-xs text-slate-500">Mean Z-Score</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-white">
            {report?.statistical_summary?.max_z_score?.toFixed(2) || '—'}
          </p>
          <p className="text-xs text-slate-500">Max Z-Score</p>
        </div>
      </div>

      {/* Breakdown Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* By Type */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">By Signal Type</h3>
          <div className="space-y-3">
            {report?.by_type && Object.entries(report.by_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-slate-400 capitalize text-sm">
                  {type.replace(/_/g, ' ')}
                </span>
                <span className="text-white font-medium">{count as number}</span>
              </div>
            ))}
            {!report?.by_type || Object.keys(report.by_type).length === 0 && (
              <p className="text-slate-500 text-center py-4">No signals detected</p>
            )}
          </div>
        </div>

        {/* By Severity */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">By Severity</h3>
          <div className="space-y-3">
            {['critical', 'high', 'medium', 'low'].map((sev) => (
              <div key={sev} className="flex items-center justify-between">
                <span className={`badge badge-${sev}`}>{sev}</span>
                <span className="text-white font-medium">
                  {(report?.by_severity as Record<string, number>)?.[sev] || 0}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* By Document */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-white mb-4">By Document</h3>
          <div className="space-y-3 max-h-48 overflow-y-auto">
            {report?.by_document && Object.entries(report.by_document).map(([doc, count]) => (
              <div key={doc} className="flex items-center justify-between">
                <span className="text-slate-400 text-sm truncate flex-1 mr-2">{doc}</span>
                <span className="text-white font-medium">{count as number}</span>
              </div>
            ))}
            {!report?.by_document || Object.keys(report.by_document).length === 0 && (
              <p className="text-slate-500 text-center py-4">No documents analyzed</p>
            )}
          </div>
        </div>
      </div>

      {/* Signals List */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">All Bias Signals</h3>
        <div className="space-y-4">
          {report?.signals?.map((signal: any) => (
            <div
              key={signal.id}
              className={`p-4 rounded-lg border ${
                Math.abs(signal.z_score) >= 2
                  ? 'bg-red-500/10 border-red-500/30'
                  : Math.abs(signal.z_score) >= 1.5
                  ? 'bg-amber-500/10 border-amber-500/30'
                  : 'bg-slate-800/50 border-slate-700/50'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className={`badge badge-${signal.severity}`}>{signal.severity}</span>
                    <span className="px-2 py-1 rounded text-xs font-medium bg-slate-700 text-slate-300 capitalize">
                      {signal.signal_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-slate-500">
                      {signal.document_name}
                    </span>
                  </div>
                  <p className="text-white">{signal.description}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className={`text-2xl font-bold ${
                    Math.abs(signal.z_score) >= 2 ? 'text-red-400' :
                    Math.abs(signal.z_score) >= 1.5 ? 'text-amber-400' :
                    'text-white'
                  }`}>
                    {signal.z_score.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">z-score</p>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-700/50 grid grid-cols-3 gap-4 text-xs">
                <div>
                  <p className="text-slate-500">Observed</p>
                  <p className="text-white">{signal.metric_value.toFixed(3)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Baseline Mean</p>
                  <p className="text-white">{signal.baseline_mean.toFixed(3)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Direction</p>
                  <p className={signal.direction === 'higher' ? 'text-red-400' : 'text-emerald-400'}>
                    {signal.direction}
                  </p>
                </div>
              </div>
            </div>
          ))}
          {!report?.signals || report.signals.length === 0 && (
            <div className="text-center py-8">
              <p className="text-slate-500">No bias signals detected</p>
              <p className="text-sm text-slate-600 mt-1">
                Analyze documents to detect statistical bias patterns
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

