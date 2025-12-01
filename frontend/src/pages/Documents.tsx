/**
 * Documents Page - Phronesis LEX
 */
import { useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../services/api';
// Document type is inferred from API response

const StatusBadge = ({ status }: { status: string }) => {
  const classes: Record<string, string> = {
    pending: 'status-pending',
    processing: 'status-processing',
    completed: 'status-completed',
    failed: 'status-failed',
    needs_review: 'status-pending',
  };

  return (
    <span className={`badge ${classes[status] || 'status-pending'}`}>
      {status === 'needs_review' ? 'Review' : status}
    </span>
  );
};

const DocTypeIcon = ({ docType }: { docType: string }) => {
  const icons: Record<string, string> = {
    section_7_report: '📋',
    section_37_report: '📋',
    psychological_report: '🧠',
    social_work_report: '👥',
    cafcass_analysis: '⚖️',
    witness_statement: '📝',
    expert_report: '🔬',
    court_order: '⚖️',
    judgment: '⚖️',
    application: '📄',
    other: '📄',
  };

  return <span className="text-2xl">{icons[docType] || '📄'}</span>;
};

export function Documents() {
  const { id: caseId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['documents', caseId, typeFilter, statusFilter],
    queryFn: () => documentsApi.forCase(caseId!, {
      doc_type: typeFilter || undefined,
      status: statusFilter || undefined,
    }),
    enabled: !!caseId,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata: any }) =>
      documentsApi.upload(caseId!, file, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', caseId] });
      setShowUploadModal(false);
    },
  });

  const handleUpload = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const file = (formData.get('file') as File);
    
    if (!file) return;

    uploadMutation.mutate({
      file,
      metadata: {
        doc_type: formData.get('doc_type'),
        title: formData.get('title'),
        date_filed: formData.get('date_filed'),
        author: formData.get('author'),
        author_role: formData.get('author_role'),
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Documents</h1>
          <p className="text-slate-400 mt-1">
            Upload and manage case documents
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload Document
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-white">{data?.count || 0}</p>
          <p className="text-xs text-slate-500">Total Documents</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-emerald-400">
            {data?.results.filter(d => d.status === 'completed').length || 0}
          </p>
          <p className="text-xs text-slate-500">Processed</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-amber-400">
            {data?.results.filter(d => d.status === 'pending' || d.status === 'processing').length || 0}
          </p>
          <p className="text-xs text-slate-500">Pending</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-purple-400">
            {data?.results.reduce((sum, d) => sum + d.claim_count, 0) || 0}
          </p>
          <p className="text-xs text-slate-500">Total Claims</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4">
        <select
          className="select w-48"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All Document Types</option>
          <option value="section_7_report">Section 7 Report</option>
          <option value="section_37_report">Section 37 Report</option>
          <option value="psychological_report">Psychological Report</option>
          <option value="social_work_report">Social Work Report</option>
          <option value="cafcass_analysis">CAFCASS Analysis</option>
          <option value="witness_statement">Witness Statement</option>
          <option value="expert_report">Expert Report</option>
          <option value="court_order">Court Order</option>
          <option value="other">Other</option>
        </select>
        <select
          className="select w-40"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Documents List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
        </div>
      ) : (
        <div className="grid gap-4">
          {data?.results.map((doc) => (
            <div key={doc.id} className="card card-hover p-4">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-slate-800 rounded-lg">
                  <DocTypeIcon docType={doc.doc_type} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <h3 className="font-medium text-white truncate">{doc.filename}</h3>
                    <StatusBadge status={doc.status} />
                    <span className="text-xs text-slate-500">{doc.doc_type_display}</span>
                  </div>
                  {doc.title && (
                    <p className="text-sm text-slate-400 truncate">{doc.title}</p>
                  )}
                  <div className="flex flex-wrap gap-4 mt-2 text-xs text-slate-500">
                    {doc.author && <span>Author: {doc.author}</span>}
                    {doc.date_filed && (
                      <span>Filed: {new Date(doc.date_filed).toLocaleDateString('en-GB')}</span>
                    )}
                    {doc.page_count > 0 && <span>{doc.page_count} pages</span>}
                    {doc.word_count > 0 && <span>{doc.word_count.toLocaleString()} words</span>}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold text-white">{doc.claim_count}</p>
                  <p className="text-xs text-slate-500">claims</p>
                  {doc.bias_signal_count > 0 && (
                    <p className="text-xs text-amber-400 mt-1">{doc.bias_signal_count} bias signals</p>
                  )}
                </div>
              </div>
            </div>
          ))}
          {data?.results.length === 0 && (
            <div className="card p-12 text-center">
              <div className="text-5xl mb-4">📁</div>
              <p className="text-slate-400 mb-4">No documents uploaded yet</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="btn-primary"
              >
                Upload your first document
              </button>
            </div>
          )}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="card p-6 w-full max-w-lg animate-fade-in">
            <h2 className="text-xl font-semibold text-white mb-4">Upload Document</h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">File *</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  name="file"
                  required
                  accept=".pdf,.doc,.docx,.txt"
                  className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-slate-700 file:text-white hover:file:bg-slate-600"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Document Type *</label>
                <select name="doc_type" required className="select">
                  <option value="section_7_report">Section 7 Report</option>
                  <option value="section_37_report">Section 37 Report</option>
                  <option value="psychological_report">Psychological Report</option>
                  <option value="social_work_report">Social Work Report</option>
                  <option value="cafcass_analysis">CAFCASS Analysis</option>
                  <option value="witness_statement">Witness Statement</option>
                  <option value="expert_report">Expert Report</option>
                  <option value="court_order">Court Order</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Title</label>
                <input name="title" className="input" placeholder="Document title" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Author</label>
                  <input name="author" className="input" placeholder="Author name" />
                </div>
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Role</label>
                  <input name="author_role" className="input" placeholder="e.g., Social Worker" />
                </div>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Date Filed</label>
                <input type="date" name="date_filed" className="input" />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex-1"
                  disabled={uploadMutation.isPending}
                >
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

