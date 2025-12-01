/**
 * Contradictions Page - Phronesis LEX
 * The revolutionary contradiction detection view
 */
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contradictionsApi } from '../services/api';
import type { Contradiction } from '../types';

const SeverityBadge = ({ severity }: { severity: string }) => {
  const classes = {
    critical: 'badge-critical',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    info: 'badge-info',
  }[severity] || 'badge-info';

  return <span className={`badge ${classes}`}>{severity}</span>;
};

const TypeBadge = ({ type }: { type: string }) => {
  const labels: Record<string, string> = {
    direct: 'Direct',
    temporal: 'Temporal',
    self: 'Self-Contradiction',
    modality: 'Modality',
    value: 'Value Mismatch',
    attribution: 'Attribution',
    quotation: 'Quotation',
    omission: 'Omission',
  };

  return (
    <span className="px-2 py-1 rounded text-xs font-medium bg-slate-700 text-slate-300">
      {labels[type] || type}
    </span>
  );
};

const ContradictionCard = ({
  contradiction,
  onResolve,
  isExpanded,
  onToggle,
}: {
  contradiction: Contradiction;
  onResolve: (id: string, note: string) => void;
  isExpanded: boolean;
  onToggle: () => void;
}) => {
  const [resolveNote, setResolveNote] = useState('');

  return (
    <div
      className={`card overflow-hidden transition-all ${
        contradiction.same_author ? 'border-l-4 border-l-red-500' : ''
      } ${contradiction.resolved ? 'opacity-60' : ''}`}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <SeverityBadge severity={contradiction.severity} />
              <TypeBadge type={contradiction.contradiction_type} />
              {contradiction.same_author && (
                <span className="px-2 py-1 rounded text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30">
                  ⚠️ LUCAS DIRECTION
                </span>
              )}
              {contradiction.resolved && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-emerald-500/20 text-emerald-300">
                  ✓ Resolved
                </span>
              )}
            </div>
            <p className="text-white">{contradiction.description}</p>
          </div>
          <div className="flex items-center gap-2 text-slate-400">
            <span className="text-xs">{Math.round(contradiction.confidence * 100)}% conf</span>
            <svg
              className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-slate-700/50">
          {/* Claims Comparison */}
          <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-700/50">
            {/* Claim A */}
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-300">
                  Claim A
                </span>
                <span className="text-xs text-slate-500">
                  {contradiction.claim_a_document_name}
                  {contradiction.claim_a_page && ` (p.${contradiction.claim_a_page})`}
                </span>
              </div>
              <blockquote className="text-sm text-slate-300 italic border-l-2 border-blue-500/50 pl-3">
                "{contradiction.claim_a_text}"
              </blockquote>
              {contradiction.claim_a_author && (
                <p className="text-xs text-slate-500 mt-2">— {contradiction.claim_a_author}</p>
              )}
            </div>

            {/* Claim B */}
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className="px-2 py-1 rounded text-xs font-medium bg-purple-500/20 text-purple-300">
                  Claim B
                </span>
                <span className="text-xs text-slate-500">
                  {contradiction.claim_b_document_name}
                  {contradiction.claim_b_page && ` (p.${contradiction.claim_b_page})`}
                </span>
              </div>
              <blockquote className="text-sm text-slate-300 italic border-l-2 border-purple-500/50 pl-3">
                "{contradiction.claim_b_text}"
              </blockquote>
              {contradiction.claim_b_author && (
                <p className="text-xs text-slate-500 mt-2">— {contradiction.claim_b_author}</p>
              )}
            </div>
          </div>

          {/* Legal Significance */}
          {contradiction.legal_significance && (
            <div className="p-4 bg-amber-500/5 border-t border-slate-700/50">
              <h4 className="text-sm font-semibold text-amber-400 mb-2">Legal Significance</h4>
              <p className="text-sm text-slate-300">{contradiction.legal_significance}</p>
            </div>
          )}

          {/* Recommended Action */}
          {contradiction.recommended_action && (
            <div className="p-4 bg-blue-500/5 border-t border-slate-700/50">
              <h4 className="text-sm font-semibold text-blue-400 mb-2">Recommended Action</h4>
              <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans">
                {contradiction.recommended_action}
              </pre>
            </div>
          )}

          {/* Resolution */}
          {!contradiction.resolved && (
            <div className="p-4 border-t border-slate-700/50">
              <h4 className="text-sm font-semibold text-slate-400 mb-2">Mark as Resolved</h4>
              <div className="flex gap-3">
                <textarea
                  className="input flex-1 text-sm"
                  placeholder="Resolution note (min 10 characters)..."
                  rows={2}
                  value={resolveNote}
                  onChange={(e) => setResolveNote(e.target.value)}
                />
                <button
                  onClick={() => {
                    onResolve(contradiction.id, resolveNote);
                    setResolveNote('');
                  }}
                  disabled={resolveNote.length < 10}
                  className="btn-secondary self-end"
                >
                  Resolve
                </button>
              </div>
            </div>
          )}

          {contradiction.resolved && contradiction.resolution_note && (
            <div className="p-4 bg-emerald-500/5 border-t border-slate-700/50">
              <h4 className="text-sm font-semibold text-emerald-400 mb-2">Resolution</h4>
              <p className="text-sm text-slate-300">{contradiction.resolution_note}</p>
              <p className="text-xs text-slate-500 mt-2">
                Resolved {contradiction.resolved_at && new Date(contradiction.resolved_at).toLocaleString()}
                {contradiction.resolved_by && ` by ${contradiction.resolved_by}`}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export function Contradictions() {
  const { id: caseId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [showResolved, setShowResolved] = useState(false);

  const { data: summary } = useQuery({
    queryKey: ['contradiction-summary', caseId],
    queryFn: () => contradictionsApi.getSummary(caseId!),
    enabled: !!caseId,
  });

  const { data, isLoading } = useQuery({
    queryKey: ['contradictions', caseId, typeFilter, severityFilter, showResolved],
    queryFn: () => contradictionsApi.forCase(caseId!, {
      type: typeFilter || undefined,
      severity: severityFilter || undefined,
      resolved: showResolved ? undefined : 'false',
    }),
    enabled: !!caseId,
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) =>
      contradictionsApi.resolve(id, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contradictions', caseId] });
      queryClient.invalidateQueries({ queryKey: ['contradiction-summary', caseId] });
    },
  });

  const detectMutation = useMutation({
    mutationFn: () => contradictionsApi.detect(caseId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contradictions', caseId] });
      queryClient.invalidateQueries({ queryKey: ['contradiction-summary', caseId] });
      queryClient.invalidateQueries({ queryKey: ['case-stats', caseId] });
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Contradiction Detection</h1>
          <p className="text-slate-400 mt-1">
            Systematic analysis of conflicting claims across documents
          </p>
        </div>
        <button
          onClick={() => detectMutation.mutate()}
          disabled={detectMutation.isPending}
          className="btn-primary flex items-center gap-2"
        >
          {detectMutation.isPending ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              Analyzing...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Re-run Detection
            </>
          )}
        </button>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="card p-4 text-center">
            <p className="text-3xl font-bold text-white">{summary.total}</p>
            <p className="text-xs text-slate-500">Total</p>
          </div>
          <div className="card p-4 text-center border-red-500/30">
            <p className="text-3xl font-bold text-red-400">{summary.self_contradictions}</p>
            <p className="text-xs text-slate-500">Self-Contradictions</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-3xl font-bold text-amber-400">{summary.unresolved}</p>
            <p className="text-xs text-slate-500">Unresolved</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-3xl font-bold text-red-400">{summary.by_severity?.critical || 0}</p>
            <p className="text-xs text-slate-500">Critical</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-3xl font-bold text-orange-400">{summary.by_severity?.high || 0}</p>
            <p className="text-xs text-slate-500">High</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4">
        <select
          className="select w-48"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Types</option>
          <option value="direct">Direct</option>
          <option value="self">Self-Contradiction</option>
          <option value="temporal">Temporal</option>
          <option value="modality">Modality</option>
          <option value="value">Value Mismatch</option>
          <option value="attribution">Attribution</option>
        </select>
        <select
          className="select w-48"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={showResolved}
            onChange={(e) => setShowResolved(e.target.checked)}
            className="rounded border-slate-600 bg-slate-800 text-red-500 focus:ring-red-500"
          />
          Show resolved
        </label>
      </div>

      {/* Contradictions List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.results.map((contradiction) => (
            <ContradictionCard
              key={contradiction.id}
              contradiction={contradiction}
              isExpanded={expandedId === contradiction.id}
              onToggle={() => setExpandedId(expandedId === contradiction.id ? null : contradiction.id)}
              onResolve={(id, note) => resolveMutation.mutate({ id, note })}
            />
          ))}
          {data?.results.length === 0 && (
            <div className="card p-12 text-center">
              <div className="text-5xl mb-4">🔍</div>
              <p className="text-slate-400 mb-4">No contradictions found</p>
              <p className="text-sm text-slate-500">
                Run contradiction detection to analyze claims across documents
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

