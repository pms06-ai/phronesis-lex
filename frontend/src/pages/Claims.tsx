/**
 * Claims Page - Phronesis LEX
 */
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { claimsApi } from '../services/api';
import type { Claim } from '../types';

const ModalityBadge = ({ modality }: { modality: string }) => {
  const classes: Record<string, string> = {
    asserted: 'modality-asserted',
    reported: 'modality-reported',
    alleged: 'modality-alleged',
    denied: 'modality-denied',
    hypothetical: 'modality-hypothetical',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${classes[modality] || 'bg-slate-700'}`}>
      {modality}
    </span>
  );
};

const ClaimCard = ({ claim }: { claim: Claim }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card p-4">
      <div className="flex items-start gap-4">
        {/* Certainty indicator */}
        <div className="flex-shrink-0 w-12 text-center">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center mx-auto"
            style={{
              background: `conic-gradient(
                ${claim.certainty >= 0.7 ? '#10b981' : claim.certainty >= 0.4 ? '#f59e0b' : '#ef4444'} 
                ${claim.certainty * 360}deg, 
                #1e293b ${claim.certainty * 360}deg
              )`,
            }}
          >
            <div className="w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center">
              <span className="text-xs font-bold text-white">{Math.round(claim.certainty * 100)}</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 mt-1">certainty</p>
        </div>

        {/* Claim content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <ModalityBadge modality={claim.modality} />
            <span className="px-2 py-1 rounded text-xs font-medium bg-slate-700 text-slate-300 capitalize">
              {claim.claim_type}
            </span>
            {claim.polarity === 'negate' && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-300">
                NEGATION
              </span>
            )}
          </div>

          <p className="text-white leading-relaxed">{claim.claim_text}</p>

          {/* Metadata */}
          <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-500">
            {claim.asserted_by && (
              <span>By: <span className="text-slate-400">{claim.asserted_by}</span></span>
            )}
            {claim.subject && (
              <span>About: <span className="text-slate-400">{claim.subject}</span></span>
            )}
            {claim.source_document && (
              <span>Doc: <span className="text-slate-400">{claim.source_document}</span></span>
            )}
            {claim.page_number && (
              <span>Page: <span className="text-slate-400">{claim.page_number}</span></span>
            )}
          </div>

          {/* Expanded details */}
          {expanded && (
            <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-3">
              {claim.source_quote && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Source Quote</p>
                  <blockquote className="text-sm text-slate-300 italic border-l-2 border-slate-600 pl-3">
                    {claim.source_quote}
                  </blockquote>
                </div>
              )}
              {claim.certainty_markers && claim.certainty_markers.length > 0 && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Certainty Markers</p>
                  <div className="flex flex-wrap gap-1">
                    {claim.certainty_markers.map((m, i) => (
                      <span key={i} className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {claim.time_expression && (
                <div>
                  <p className="text-xs text-slate-500 mb-1">Temporal Reference</p>
                  <p className="text-sm text-slate-300">{claim.time_expression}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Expand toggle */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-slate-500 hover:text-slate-300"
        >
          <svg
            className={`w-5 h-5 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export function Claims() {
  const { id: caseId } = useParams<{ id: string }>();
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [modalityFilter, setModalityFilter] = useState<string>('');
  const [authorFilter, setAuthorFilter] = useState<string>('');
  const [minCertainty, setMinCertainty] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['claims', caseId, typeFilter, modalityFilter, authorFilter, minCertainty],
    queryFn: () => claimsApi.forCase(caseId!, {
      claim_type: typeFilter || undefined,
      modality: modalityFilter || undefined,
      asserted_by: authorFilter || undefined,
      min_certainty: minCertainty || undefined,
    }),
    enabled: !!caseId,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Claims</h1>
        <p className="text-slate-400 mt-1">
          Extracted claims with epistemic annotation
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-white">{data?.count || 0}</p>
          <p className="text-xs text-slate-500">Total Claims</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4">
        <select
          className="select w-40"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Types</option>
          <option value="assertion">Assertion</option>
          <option value="allegation">Allegation</option>
          <option value="finding">Finding</option>
          <option value="conclusion">Conclusion</option>
          <option value="recommendation">Recommendation</option>
          <option value="opinion">Opinion</option>
        </select>
        <select
          className="select w-40"
          value={modalityFilter}
          onChange={(e) => setModalityFilter(e.target.value)}
        >
          <option value="">All Modalities</option>
          <option value="asserted">Asserted</option>
          <option value="reported">Reported</option>
          <option value="alleged">Alleged</option>
          <option value="denied">Denied</option>
          <option value="hypothetical">Hypothetical</option>
        </select>
        <input
          type="text"
          placeholder="Filter by author..."
          className="input w-48"
          value={authorFilter}
          onChange={(e) => setAuthorFilter(e.target.value)}
        />
        <input
          type="number"
          placeholder="Min certainty..."
          className="input w-36"
          min="0"
          max="1"
          step="0.1"
          value={minCertainty}
          onChange={(e) => setMinCertainty(e.target.value)}
        />
      </div>

      {/* Claims List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      ) : (
        <div className="space-y-3">
          {data?.results.map((claim) => (
            <ClaimCard key={claim.id} claim={claim} />
          ))}
          {data?.results.length === 0 && (
            <div className="card p-12 text-center">
              <p className="text-slate-400">No claims extracted yet</p>
              <p className="text-sm text-slate-500 mt-2">
                Upload and analyze documents to extract claims
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

