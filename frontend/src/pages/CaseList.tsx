/**
 * Case List Page - Phronesis LEX
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { casesApi } from '../services/api';
// Type is inferred from API response

export function CaseList() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['cases', statusFilter, typeFilter, searchTerm],
    queryFn: () => casesApi.list({
      status: statusFilter || undefined,
      case_type: typeFilter || undefined,
      search: searchTerm || undefined,
    }),
  });

  const createMutation = useMutation({
    mutationFn: casesApi.create,
    onSuccess: (newCase) => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
      navigate(`/cases/${newCase.id}`);
    },
  });

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    createMutation.mutate({
      reference: formData.get('reference') as string,
      title: formData.get('title') as string || null,
      case_type: formData.get('case_type') as string || 'private_law',
      court: formData.get('court') as string || null,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Cases</h1>
          <p className="text-slate-400 mt-1">Manage and analyze family court cases</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Case
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search cases..."
            className="input"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          className="select w-48"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="closed">Closed</option>
          <option value="archived">Archived</option>
        </select>
        <select
          className="select w-48"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Types</option>
          <option value="private_law">Private Law</option>
          <option value="public_law">Public Law</option>
          <option value="adoption">Adoption</option>
          <option value="financial">Financial</option>
          <option value="domestic_abuse">Domestic Abuse</option>
        </select>
      </div>

      {/* Case List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      ) : (
        <div className="grid gap-4">
          {data?.results.map((caseItem) => (
            <Link
              key={caseItem.id}
              to={`/cases/${caseItem.id}`}
              className="card card-hover p-6 block"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-white">{caseItem.reference}</h3>
                    <span className={`badge ${
                      caseItem.status === 'active' ? 'status-active' : 
                      caseItem.status === 'pending' ? 'status-pending' : 
                      'status-completed'
                    }`}>
                      {caseItem.status}
                    </span>
                    <span className="badge bg-slate-700 text-slate-300">
                      {caseItem.case_type_display}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1">{caseItem.title || 'Untitled'}</p>
                </div>
                {caseItem.next_hearing_date && (
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Next Hearing</p>
                    <p className="text-sm text-amber-400">
                      {new Date(caseItem.next_hearing_date).toLocaleDateString('en-GB')}
                    </p>
                  </div>
                )}
              </div>
              <div className="flex gap-6 mt-4 pt-4 border-t border-slate-700/50">
                <div className="text-center">
                  <p className="text-2xl font-bold text-white">{caseItem.document_count}</p>
                  <p className="text-xs text-slate-500">Documents</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-white">{caseItem.claim_count}</p>
                  <p className="text-xs text-slate-500">Claims</p>
                </div>
                <div className="text-center">
                  <p className={`text-2xl font-bold ${caseItem.contradiction_count > 0 ? 'text-red-400' : 'text-white'}`}>
                    {caseItem.contradiction_count}
                  </p>
                  <p className="text-xs text-slate-500">Contradictions</p>
                </div>
              </div>
            </Link>
          ))}
          {data?.results.length === 0 && (
            <div className="card p-12 text-center">
              <p className="text-slate-400">No cases found</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-primary mt-4"
              >
                Create your first case
              </button>
            </div>
          )}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-md animate-fade-in">
            <h2 className="text-xl font-semibold text-white mb-4">Create New Case</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Case Reference *</label>
                <input
                  name="reference"
                  required
                  className="input"
                  placeholder="e.g., FD23/12345"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Title</label>
                <input
                  name="title"
                  className="input"
                  placeholder="e.g., Re A (Children)"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Case Type</label>
                <select name="case_type" className="select">
                  <option value="private_law">Private Law (Child Arrangements)</option>
                  <option value="public_law">Public Law (Care Proceedings)</option>
                  <option value="adoption">Adoption</option>
                  <option value="financial">Financial Remedies</option>
                  <option value="domestic_abuse">Domestic Abuse</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Court</label>
                <input
                  name="court"
                  className="input"
                  placeholder="e.g., Central Family Court"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

