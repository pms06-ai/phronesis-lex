/**
 * Legal Rules Page - Phronesis LEX
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { legalRulesApi } from '../services/api';
import type { LegalRule } from '../types';

const CategoryBadge = ({ category }: { category: string }) => {
  const colors: Record<string, string> = {
    welfare: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    threshold: 'bg-red-500/20 text-red-300 border-red-500/30',
    evidence: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    professional: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    procedural: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium border ${colors[category] || colors.evidence}`}>
      {category}
    </span>
  );
};

const RuleCard = ({ rule }: { rule: LegalRule }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <CategoryBadge category={rule.category} />
              <span className="text-xs text-slate-500 font-mono">{rule.rule_id}</span>
            </div>
            <h3 className="font-semibold text-white">{rule.short_name}</h3>
            <p className="text-sm text-slate-400 mt-1">{rule.full_citation}</p>
          </div>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform flex-shrink-0 ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-700/50 p-4 bg-slate-800/30">
          <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">{rule.text}</p>
          
          {rule.keywords.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-700/50">
              <p className="text-xs text-slate-500 mb-2">Keywords</p>
              <div className="flex flex-wrap gap-2">
                {rule.keywords.map((kw, i) => (
                  <span key={i} className="px-2 py-1 rounded text-xs bg-slate-700 text-slate-300">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export function LegalRules() {
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['legal-rules', categoryFilter, searchTerm],
    queryFn: () => legalRulesApi.list({
      category: categoryFilter || undefined,
      search: searchTerm || undefined,
    }),
  });

  // Group rules by category
  const groupedRules = data?.results.reduce((acc, rule) => {
    const cat = rule.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(rule);
    return acc;
  }, {} as Record<string, LegalRule[]>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Legal Rules Library</h1>
        <p className="text-slate-400 mt-1">
          UK Family Court legal rules, case law, and practice directions
        </p>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search rules..."
            className="input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="select w-48"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All Categories</option>
          <option value="welfare">Welfare</option>
          <option value="threshold">Threshold</option>
          <option value="evidence">Evidence</option>
          <option value="professional">Professional</option>
          <option value="procedural">Procedural</option>
        </select>
      </div>

      {/* Rules */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      ) : categoryFilter ? (
        // Filtered view
        <div className="space-y-3">
          {data?.results.map((rule) => (
            <RuleCard key={rule.rule_id} rule={rule} />
          ))}
          {data?.results.length === 0 && (
            <div className="card p-12 text-center">
              <p className="text-slate-400">No rules found</p>
            </div>
          )}
        </div>
      ) : (
        // Grouped view
        <div className="space-y-8">
          {groupedRules && Object.entries(groupedRules).map(([category, rules]) => (
            <div key={category}>
              <div className="flex items-center gap-3 mb-4">
                <CategoryBadge category={category} />
                <h2 className="text-lg font-semibold text-white capitalize">{category} Rules</h2>
                <span className="text-sm text-slate-500">({rules.length})</span>
              </div>
              <div className="space-y-3">
                {rules.map((rule) => (
                  <RuleCard key={rule.rule_id} rule={rule} />
                ))}
              </div>
            </div>
          ))}
          {!groupedRules || Object.keys(groupedRules).length === 0 && (
            <div className="card p-12 text-center">
              <p className="text-slate-400">No legal rules loaded</p>
              <p className="text-sm text-slate-500 mt-2">
                Run: python manage.py seed_legal_rules
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

