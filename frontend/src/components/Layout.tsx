/**
 * Layout Component - Phronesis LEX
 * Main application layout with navigation
 */
import { ReactNode, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { casesApi } from '../services/api';

interface LayoutProps {
  children: ReactNode;
}

const Logo = () => (
  <div className="flex items-center gap-3">
    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600 to-red-700 flex items-center justify-center shadow-lg shadow-red-900/30">
      <span className="text-white font-bold text-xl font-serif">Φ</span>
    </div>
    <div>
      <h1 className="text-lg font-semibold text-white tracking-tight">Phronesis</h1>
      <p className="text-[10px] text-slate-400 uppercase tracking-widest">LEX</p>
    </div>
  </div>
);

const NavLink = ({
  to,
  icon,
  children,
  badge,
}: {
  to: string;
  icon: ReactNode;
  children: ReactNode;
  badge?: number;
}) => {
  const location = useLocation();
  const isActive = location.pathname === to || location.pathname.startsWith(to + '/');

  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 group ${
        isActive
          ? 'bg-red-600/20 text-red-300 border-l-2 border-red-500'
          : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
      }`}
    >
      <span className={`${isActive ? 'text-red-400' : 'text-slate-500 group-hover:text-slate-300'}`}>
        {icon}
      </span>
      <span className="flex-1 font-medium text-sm">{children}</span>
      {badge !== undefined && badge > 0 && (
        <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-300">
          {badge}
        </span>
      )}
    </Link>
  );
};

const CaseNavLink = ({
  to,
  icon,
  children,
  badge,
}: {
  to: string;
  icon: ReactNode;
  children: ReactNode;
  badge?: number;
}) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-3 py-2 rounded-md transition-all duration-200 text-sm ${
        isActive
          ? 'bg-slate-700/70 text-white'
          : 'text-slate-400 hover:text-white hover:bg-slate-700/30'
      }`}
    >
      <span className="text-slate-500">{icon}</span>
      <span className="flex-1">{children}</span>
      {badge !== undefined && badge > 0 && (
        <span className="px-1.5 py-0.5 rounded text-xs bg-slate-600 text-slate-200">
          {badge}
        </span>
      )}
    </Link>
  );
};

// Icons
const HomeIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

const FolderIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

const BookIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const DocIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const ClaimIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
  </svg>
);

const ContradictionIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);

const BiasIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
  </svg>
);

const TimelineIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const ArgumentIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
  </svg>
);

export function Layout({ children }: LayoutProps) {
  const { id: caseId } = useParams();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => casesApi.get(caseId!),
    enabled: !!caseId,
  });

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-20'
        } flex-shrink-0 border-r border-slate-700/50 bg-slate-900/50 backdrop-blur-sm transition-all duration-300`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-slate-700/50">
            {sidebarOpen && <Logo />}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-slate-700/50 text-slate-400"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {sidebarOpen && (
              <>
                <NavLink to="/" icon={<HomeIcon />}>Dashboard</NavLink>
                <NavLink to="/cases" icon={<FolderIcon />}>Cases</NavLink>
                <NavLink to="/legal-rules" icon={<BookIcon />}>Legal Rules</NavLink>

                {/* Case Sub-Navigation */}
                {caseId && caseData && (
                  <div className="pt-4 mt-4 border-t border-slate-700/50">
                    <div className="px-4 py-2 mb-2">
                      <p className="text-xs text-slate-500 uppercase tracking-wider">Current Case</p>
                      <p className="text-sm font-medium text-white truncate">{caseData.reference}</p>
                    </div>
                    <div className="space-y-1">
                      <CaseNavLink to={`/cases/${caseId}`} icon={<FolderIcon />}>
                        Overview
                      </CaseNavLink>
                      <CaseNavLink to={`/cases/${caseId}/documents`} icon={<DocIcon />} badge={caseData.document_count}>
                        Documents
                      </CaseNavLink>
                      <CaseNavLink to={`/cases/${caseId}/claims`} icon={<ClaimIcon />} badge={caseData.claim_count}>
                        Claims
                      </CaseNavLink>
                      <CaseNavLink to={`/cases/${caseId}/contradictions`} icon={<ContradictionIcon />} badge={caseData.contradiction_count}>
                        Contradictions
                      </CaseNavLink>
                      <CaseNavLink to={`/cases/${caseId}/bias`} icon={<BiasIcon />} badge={caseData.bias_signal_count}>
                        Bias Analysis
                      </CaseNavLink>
                      <CaseNavLink to={`/cases/${caseId}/timeline`} icon={<TimelineIcon />}>
                        Timeline
                      </CaseNavLink>
                      <CaseNavLink to={`/cases/${caseId}/arguments`} icon={<ArgumentIcon />}>
                        Arguments
                      </CaseNavLink>
                    </div>
                  </div>
                )}
              </>
            )}
          </nav>

          {/* Footer */}
          {sidebarOpen && (
            <div className="p-4 border-t border-slate-700/50">
              <p className="text-xs text-slate-500">FCIP v5.0</p>
              <p className="text-xs text-slate-600">UK Family Court Analysis</p>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}

