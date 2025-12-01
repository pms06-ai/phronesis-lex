/**
 * Dashboard Page - Phronesis LEX
 * Main overview with statistics and recent activity
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { casesApi } from '../services/api';

const StatCard = ({
  label,
  value,
  icon,
  color = 'red',
  delay = 0,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  color?: string;
  delay?: number;
}) => {
  const colorClasses = {
    red: 'from-red-600/20 to-red-900/10 border-red-500/20',
    blue: 'from-blue-600/20 to-blue-900/10 border-blue-500/20',
    green: 'from-emerald-600/20 to-emerald-900/10 border-emerald-500/20',
    amber: 'from-amber-600/20 to-amber-900/10 border-amber-500/20',
    purple: 'from-purple-600/20 to-purple-900/10 border-purple-500/20',
  }[color];

  const iconClasses = {
    red: 'text-red-400',
    blue: 'text-blue-400',
    green: 'text-emerald-400',
    amber: 'text-amber-400',
    purple: 'text-purple-400',
  }[color];

  return (
    <div
      className={`relative card p-6 bg-gradient-to-br ${colorClasses} animate-fade-in opacity-0`}
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{label}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
        </div>
        <div className={`p-3 rounded-lg bg-slate-800/50 ${iconClasses}`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

export function Dashboard() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: casesApi.getDashboard,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-fade-in">
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Forensic Case Intelligence Platform Overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Active Cases"
          value={dashboard?.active_cases || 0}
          color="blue"
          delay={100}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          }
        />
        <StatCard
          label="Total Documents"
          value={dashboard?.total_documents || 0}
          color="green"
          delay={200}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
        <StatCard
          label="Claims Extracted"
          value={dashboard?.total_claims || 0}
          color="purple"
          delay={300}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          }
        />
        <StatCard
          label="Unresolved Contradictions"
          value={dashboard?.unresolved_contradictions || 0}
          color="red"
          delay={400}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </div>

      {/* Recent Cases & Upcoming Hearings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Cases */}
        <div className="card p-6 animate-fade-in" style={{ animationDelay: '500ms', animationFillMode: 'forwards' }}>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Recent Cases</h2>
            <Link to="/cases" className="text-sm text-red-400 hover:text-red-300">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {dashboard?.recent_cases && dashboard.recent_cases.length > 0 ? (
              dashboard.recent_cases.map((c) => (
                <Link
                  key={c.id}
                  to={`/cases/${c.id}`}
                  className="block p-4 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 transition-colors border border-slate-700/50"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-white">{c.reference}</p>
                      <p className="text-sm text-slate-400 mt-1">{c.title || 'Untitled'}</p>
                    </div>
                    <span className={`badge ${c.status === 'active' ? 'status-active' : 'status-pending'}`}>
                      {c.status}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-3 text-xs text-slate-500">
                    <span>{c.document_count} docs</span>
                    <span>{c.claim_count} claims</span>
                    {c.contradiction_count > 0 && (
                      <span className="text-red-400">{c.contradiction_count} contradictions</span>
                    )}
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-slate-500 text-center py-8">No cases yet</p>
            )}
          </div>
        </div>

        {/* Upcoming Hearings */}
        <div className="card p-6 animate-fade-in" style={{ animationDelay: '600ms', animationFillMode: 'forwards' }}>
          <h2 className="text-lg font-semibold text-white mb-6">Upcoming Hearings</h2>
          <div className="space-y-3">
            {dashboard?.upcoming_hearings && dashboard.upcoming_hearings.length > 0 ? (
              dashboard.upcoming_hearings.map((c) => (
                <Link
                  key={c.id}
                  to={`/cases/${c.id}`}
                  className="block p-4 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 transition-colors border border-slate-700/50"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-white">{c.reference}</p>
                      <p className="text-sm text-slate-400">{c.title || 'Untitled'}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-amber-400">
                        {c.next_hearing_date ? new Date(c.next_hearing_date).toLocaleDateString('en-GB', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric'
                        }) : 'TBD'}
                      </p>
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-slate-500 text-center py-8">No upcoming hearings</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6 animate-fade-in" style={{ animationDelay: '700ms', animationFillMode: 'forwards' }}>
        <h2 className="text-lg font-semibold text-white mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/cases"
            className="p-4 rounded-lg bg-gradient-to-br from-blue-600/20 to-blue-900/10 border border-blue-500/20 hover:border-blue-500/40 transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400 group-hover:bg-blue-500/30 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <span className="font-medium text-white">New Case</span>
            </div>
          </Link>
          
          <Link
            to="/legal-rules"
            className="p-4 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-900/10 border border-purple-500/20 hover:border-purple-500/40 transition-colors group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20 text-purple-400 group-hover:bg-purple-500/30 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <span className="font-medium text-white">Legal Rules</span>
            </div>
          </Link>
          
          <div className="p-4 rounded-lg bg-gradient-to-br from-emerald-600/20 to-emerald-900/10 border border-emerald-500/20 opacity-50">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="font-medium text-white">Generate Report</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

