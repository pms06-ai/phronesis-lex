/**
 * Arguments Page - Phronesis LEX
 * Toulmin-structured legal arguments
 */
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { argumentsApi } from '../services/api';
import type { ToulminArgument } from '../types';

const ArgumentCard = ({ argument }: { argument: ToulminArgument }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-300">
                {argument.qualifier}
              </span>
              {argument.warrant_rule_name && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-slate-700 text-slate-300">
                  {argument.warrant_rule_name}
                </span>
              )}
            </div>
            <p className="text-white font-medium">{argument.claim_text}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="flex items-center gap-1">
              <span className="text-xs text-slate-500">Confidence:</span>
              <span className="text-sm font-bold text-white">
                {Math.round(argument.confidence_mean * 100)}%
              </span>
            </div>
            <svg
              className={`w-5 h-5 text-slate-400 mt-2 transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Toulmin Structure */}
      {expanded && (
        <div className="border-t border-slate-700/50">
          {/* Grounds */}
          <div className="p-4 border-b border-slate-700/50">
            <h4 className="text-sm font-semibold text-blue-400 mb-2">Grounds (Evidence)</h4>
            <ul className="space-y-2">
              {argument.grounds.map((ground, i) => (
                <li key={i} className="text-sm text-slate-300 pl-4 border-l-2 border-blue-500/30">
                  {ground}
                </li>
              ))}
              {argument.grounds.length === 0 && (
                <li className="text-sm text-slate-500 italic">No grounds specified</li>
              )}
            </ul>
          </div>

          {/* Warrant */}
          <div className="p-4 border-b border-slate-700/50 bg-slate-800/30">
            <h4 className="text-sm font-semibold text-purple-400 mb-2">Warrant (Legal Rule)</h4>
            <p className="text-sm text-slate-300">{argument.warrant}</p>
          </div>

          {/* Backing */}
          {argument.backing.length > 0 && (
            <div className="p-4 border-b border-slate-700/50">
              <h4 className="text-sm font-semibold text-emerald-400 mb-2">Backing (Authority)</h4>
              <div className="flex flex-wrap gap-2">
                {argument.backing.map((back, i) => (
                  <span key={i} className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-300">
                    {back}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Rebuttal */}
          {argument.rebuttal.length > 0 && (
            <div className="p-4 border-b border-slate-700/50 bg-red-500/5">
              <h4 className="text-sm font-semibold text-red-400 mb-2">Rebuttal (Unless...)</h4>
              <ul className="space-y-1">
                {argument.rebuttal.map((reb, i) => (
                  <li key={i} className="text-sm text-slate-300">• {reb}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Falsifiability */}
          {argument.falsifiability_conditions.length > 0 && (
            <div className="p-4 border-b border-slate-700/50">
              <h4 className="text-sm font-semibold text-amber-400 mb-2">Falsifiability Tests</h4>
              <ul className="space-y-1">
                {argument.falsifiability_conditions.map((cond: any, i) => (
                  <li key={i} className="text-sm text-slate-300">
                    <span className="text-amber-300">{cond.type}:</span> {cond.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Evidence */}
          {argument.missing_evidence.length > 0 && (
            <div className="p-4 border-b border-slate-700/50 bg-amber-500/5">
              <h4 className="text-sm font-semibold text-amber-400 mb-2">⚠️ Missing Evidence</h4>
              <ul className="space-y-1">
                {argument.missing_evidence.map((me, i) => (
                  <li key={i} className="text-sm text-slate-300">• {me}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Alternative Explanations */}
          {argument.alternative_explanations.length > 0 && (
            <div className="p-4">
              <h4 className="text-sm font-semibold text-slate-400 mb-2">Alternative Explanations</h4>
              <ul className="space-y-1">
                {argument.alternative_explanations.map((alt, i) => (
                  <li key={i} className="text-sm text-slate-400">• {alt}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Confidence Range */}
          <div className="p-4 bg-slate-800/50 border-t border-slate-700/50">
            <h4 className="text-xs font-semibold text-slate-500 mb-2">Confidence Range</h4>
            <div className="flex items-center gap-4">
              <span className="text-xs text-slate-500">{Math.round(argument.confidence_lower * 100)}%</span>
              <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden relative">
                <div
                  className="absolute h-full bg-gradient-to-r from-slate-600 to-blue-500"
                  style={{
                    left: `${argument.confidence_lower * 100}%`,
                    right: `${100 - argument.confidence_upper * 100}%`,
                  }}
                />
                <div
                  className="absolute w-3 h-3 -top-0.5 bg-blue-400 rounded-full border-2 border-white"
                  style={{ left: `calc(${argument.confidence_mean * 100}% - 6px)` }}
                />
              </div>
              <span className="text-xs text-slate-500">{Math.round(argument.confidence_upper * 100)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export function Arguments() {
  const { id: caseId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [showGenerateModal, setShowGenerateModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['arguments', caseId],
    queryFn: () => argumentsApi.forCase(caseId!),
    enabled: !!caseId,
  });

  const generateMutation = useMutation({
    mutationFn: ({ findingType, claimText }: { findingType: string; claimText?: string }) =>
      argumentsApi.generate(caseId!, findingType, claimText),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['arguments', caseId] });
      setShowGenerateModal(false);
    },
  });

  const handleGenerate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    generateMutation.mutate({
      findingType: formData.get('finding_type') as string,
      claimText: formData.get('claim_text') as string || undefined,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Toulmin Arguments</h1>
          <p className="text-slate-400 mt-1">
            Structured legal arguments with falsifiability conditions
          </p>
        </div>
        <button
          onClick={() => setShowGenerateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Generate Argument
        </button>
      </div>

      {/* Arguments List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.results.map((argument) => (
            <ArgumentCard key={argument.id} argument={argument} />
          ))}
          {data?.results.length === 0 && (
            <div className="card p-12 text-center">
              <div className="text-5xl mb-4">📋</div>
              <p className="text-slate-400 mb-4">No arguments generated yet</p>
              <button
                onClick={() => setShowGenerateModal(true)}
                className="btn-primary"
              >
                Generate your first argument
              </button>
            </div>
          )}
        </div>
      )}

      {/* Generate Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-lg animate-fade-in">
            <h2 className="text-xl font-semibold text-white mb-4">Generate Toulmin Argument</h2>
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Finding Type *</label>
                <select name="finding_type" required className="select">
                  <option value="welfare">Welfare Assessment (CA 1989 s1)</option>
                  <option value="threshold">Threshold Criteria (CA 1989 s31)</option>
                  <option value="credibility">Credibility Finding (Lucas)</option>
                  <option value="expert">Expert Opinion (PD25C)</option>
                  <option value="bias">Bias Finding</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Custom Claim (optional)</label>
                <textarea
                  name="claim_text"
                  className="input"
                  rows={3}
                  placeholder="Override the auto-generated claim text..."
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={generateMutation.isPending}
                >
                  {generateMutation.isPending ? 'Generating...' : 'Generate'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

