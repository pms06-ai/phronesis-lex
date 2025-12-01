/**
 * AI Subscription Workflow Page
 *
 * This page enables the copy-paste workflow with AI subscription platforms:
 * 1. Generate optimized prompts from documents/claims
 * 2. Copy prompts to Claude, ChatGPT, Grok, etc.
 * 3. Paste AI responses back to import structured data
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { promptsApi, documentsApi, claimsApi } from '../services/api';
import type { GeneratedPrompt, ParseResult, WorkflowStatus } from '../services/api';

// Simple clipboard copy function
const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      return true;
    } catch {
      return false;
    } finally {
      document.body.removeChild(textarea);
    }
  }
};

type PromptTypeKey =
  | 'claim_extraction'
  | 'document_summary'
  | 'credibility_assessment'
  | 'claim_analysis'
  | 'contradiction_analysis'
  | 'timeline_extraction'
  | 'legal_framework';

const PROMPT_TYPE_LABELS: Record<PromptTypeKey, string> = {
  claim_extraction: 'Extract Claims',
  document_summary: 'Summarize Document',
  credibility_assessment: 'Assess Credibility',
  claim_analysis: 'Analyze Claim',
  contradiction_analysis: 'Analyze Contradiction',
  timeline_extraction: 'Extract Timeline',
  legal_framework: 'Legal Framework Analysis',
};

export default function AIWorkflow() {
  const { caseId } = useParams<{ caseId: string }>();

  // State
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [documents, setDocuments] = useState<Array<{ id: string; filename: string }>>([]);
  const [claims, setClaims] = useState<Array<{ id: string; claim_text: string }>>([]);
  const [selectedPromptType, setSelectedPromptType] = useState<PromptTypeKey>('claim_extraction');
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [selectedClaimId, setSelectedClaimId] = useState<string>('');
  const [selectedClaimBId, setSelectedClaimBId] = useState<string>('');
  const [author, setAuthor] = useState<string>('');
  const [situation, setSituation] = useState<string>('');
  const [generatedPrompt, setGeneratedPrompt] = useState<GeneratedPrompt | null>(null);
  const [aiResponse, setAiResponse] = useState<string>('');
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [copySuccess, setCopySuccess] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'generate' | 'import'>('generate');

  // Load workflow status and documents
  useEffect(() => {
    if (caseId) {
      loadData();
    }
  }, [caseId]);

  const loadData = async () => {
    if (!caseId) return;

    try {
      setLoading(true);
      const [status, docs, claimsData] = await Promise.all([
        promptsApi.getWorkflowStatus(caseId),
        documentsApi.forCase(caseId),
        claimsApi.forCase(caseId),
      ]);

      setWorkflowStatus(status);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const docsResponse = docs as any;
      setDocuments(
        (docsResponse.documents || docsResponse.results || []).map((d: { id: string; filename: string }) => ({
          id: d.id,
          filename: d.filename,
        }))
      );
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const claimsResponse = claimsData as any;
      setClaims(
        (claimsResponse.claims || claimsResponse.results || []).map(
          (c: { id: string; claim_text: string }) => ({
            id: c.id,
            claim_text: c.claim_text,
          })
        )
      );
    } catch (err) {
      setError('Failed to load workflow data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePrompt = async () => {
    setError('');
    setGeneratedPrompt(null);
    setLoading(true);

    try {
      let prompt: GeneratedPrompt;

      switch (selectedPromptType) {
        case 'claim_extraction':
          if (!selectedDocId) throw new Error('Please select a document');
          prompt = await promptsApi.generateClaimExtraction(selectedDocId);
          break;
        case 'document_summary':
          if (!selectedDocId) throw new Error('Please select a document');
          prompt = await promptsApi.generateDocumentSummary(selectedDocId);
          break;
        case 'credibility_assessment':
          if (!selectedDocId) throw new Error('Please select a document');
          if (!author.trim()) throw new Error('Please enter the document author');
          prompt = await promptsApi.generateCredibilityAssessment(selectedDocId, author);
          break;
        case 'claim_analysis':
          if (!selectedClaimId) throw new Error('Please select a claim');
          prompt = await promptsApi.generateClaimAnalysis(selectedClaimId);
          break;
        case 'contradiction_analysis':
          if (!selectedClaimId || !selectedClaimBId)
            throw new Error('Please select both claims to compare');
          prompt = await promptsApi.generateContradictionAnalysis(selectedClaimId, selectedClaimBId);
          break;
        case 'timeline_extraction':
          if (!caseId) throw new Error('No case selected');
          prompt = await promptsApi.generateTimeline(caseId);
          break;
        case 'legal_framework':
          if (!caseId) throw new Error('No case selected');
          if (!situation.trim()) throw new Error('Please describe the situation');
          prompt = await promptsApi.generateLegalFramework(caseId, situation);
          break;
        default:
          throw new Error('Unknown prompt type');
      }

      setGeneratedPrompt(prompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPrompt = async () => {
    if (!generatedPrompt) return;

    const success = await copyToClipboard(generatedPrompt.full_prompt);
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } else {
      setError('Failed to copy to clipboard');
    }
  };

  const handleParseResponse = async () => {
    if (!aiResponse.trim()) {
      setError('Please paste the AI response');
      return;
    }

    setError('');
    setParseResult(null);
    setLoading(true);

    try {
      const result = await promptsApi.parseResponse(
        aiResponse,
        selectedPromptType,
        caseId,
        selectedDocId || undefined
      );
      setParseResult(result);

      if (result.success) {
        // Reload workflow status to reflect new data
        if (caseId) {
          const status = await promptsApi.getWorkflowStatus(caseId);
          setWorkflowStatus(status);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse response');
    } finally {
      setLoading(false);
    }
  };

  const renderPromptTypeSelector = () => {
    const needsDocument = ['claim_extraction', 'document_summary', 'credibility_assessment'];
    const needsClaim = ['claim_analysis'];
    const needsTwoClaims = ['contradiction_analysis'];
    const needsSituation = ['legal_framework'];

    return (
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Analysis Type</label>
          <select
            value={selectedPromptType}
            onChange={(e) => setSelectedPromptType(e.target.value as PromptTypeKey)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            {Object.entries(PROMPT_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {needsDocument.includes(selectedPromptType) && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Document</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">-- Select a document --</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedPromptType === 'credibility_assessment' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Document Author</label>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="e.g., Social Worker Jane Smith"
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        )}

        {needsClaim.includes(selectedPromptType) && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Claim</label>
            <select
              value={selectedClaimId}
              onChange={(e) => setSelectedClaimId(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">-- Select a claim --</option>
              {claims.map((claim) => (
                <option key={claim.id} value={claim.id}>
                  {claim.claim_text?.substring(0, 100)}...
                </option>
              ))}
            </select>
          </div>
        )}

        {needsTwoClaims.includes(selectedPromptType) && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Claim A</label>
              <select
                value={selectedClaimId}
                onChange={(e) => setSelectedClaimId(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="">-- Select first claim --</option>
                {claims.map((claim) => (
                  <option key={claim.id} value={claim.id}>
                    {claim.claim_text?.substring(0, 100)}...
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Claim B</label>
              <select
                value={selectedClaimBId}
                onChange={(e) => setSelectedClaimBId(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="">-- Select second claim --</option>
                {claims
                  .filter((c) => c.id !== selectedClaimId)
                  .map((claim) => (
                    <option key={claim.id} value={claim.id}>
                      {claim.claim_text?.substring(0, 100)}...
                    </option>
                  ))}
              </select>
            </div>
          </>
        )}

        {needsSituation.includes(selectedPromptType) && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Describe the Situation
            </label>
            <textarea
              value={situation}
              onChange={(e) => setSituation(e.target.value)}
              placeholder="Describe the key situation or issue requiring legal framework analysis..."
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        )}

        <button
          onClick={handleGeneratePrompt}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Prompt'}
        </button>
      </div>
    );
  };

  const renderGeneratedPrompt = () => {
    if (!generatedPrompt) return null;

    return (
      <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="font-semibold text-gray-900">Generated Prompt</h3>
            <p className="text-sm text-gray-500">
              ~{generatedPrompt.estimated_tokens.toLocaleString()} tokens
            </p>
          </div>
          <button
            onClick={handleCopyPrompt}
            className={`px-4 py-2 rounded-md text-white ${
              copySuccess ? 'bg-green-600' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {copySuccess ? 'Copied!' : 'Copy to Clipboard'}
          </button>
        </div>

        <div className="mb-3 flex flex-wrap gap-2">
          <span className="text-sm text-gray-600">Best for:</span>
          {generatedPrompt.recommended_platforms.map((platform) => (
            <span
              key={platform}
              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
            >
              {platform}
            </span>
          ))}
        </div>

        {generatedPrompt.notes && (
          <p className="text-sm text-amber-700 bg-amber-50 p-2 rounded mb-3">
            {generatedPrompt.notes}
          </p>
        )}

        <div className="bg-white border border-gray-300 rounded p-3 max-h-96 overflow-y-auto">
          <pre className="text-sm whitespace-pre-wrap font-mono">{generatedPrompt.full_prompt}</pre>
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Next Steps:</h4>
          <ol className="list-decimal list-inside text-sm text-blue-800 space-y-1">
            <li>Copy the prompt above</li>
            <li>Paste into your AI platform (Claude, ChatGPT, Grok, etc.)</li>
            <li>Copy the AI's JSON response</li>
            <li>Switch to the "Import Response" tab and paste it there</li>
          </ol>
        </div>
      </div>
    );
  };

  const renderImportTab = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Response Type</label>
        <select
          value={selectedPromptType}
          onChange={(e) => setSelectedPromptType(e.target.value as PromptTypeKey)}
          className="w-full border border-gray-300 rounded-md px-3 py-2"
        >
          {Object.entries(PROMPT_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Paste AI Response (JSON)
        </label>
        <textarea
          value={aiResponse}
          onChange={(e) => setAiResponse(e.target.value)}
          placeholder="Paste the complete AI response here..."
          rows={12}
          className="w-full border border-gray-300 rounded-md px-3 py-2 font-mono text-sm"
        />
      </div>

      <button
        onClick={handleParseResponse}
        disabled={loading || !aiResponse.trim()}
        className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? 'Parsing...' : 'Import Response'}
      </button>

      {parseResult && (
        <div
          className={`p-4 rounded-lg ${
            parseResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
          } border`}
        >
          <h3 className={`font-semibold ${parseResult.success ? 'text-green-800' : 'text-red-800'}`}>
            {parseResult.success ? 'Successfully Imported!' : 'Import Failed'}
          </h3>

          {parseResult.stored && (
            <div className="mt-2 text-sm text-green-700">
              <p>Claims imported: {parseResult.stored.claims}</p>
              <p>Timeline events imported: {parseResult.stored.events}</p>
            </div>
          )}

          {parseResult.warnings && parseResult.warnings.length > 0 && (
            <div className="mt-2 text-sm text-amber-700">
              <p className="font-medium">Warnings:</p>
              <ul className="list-disc list-inside">
                {parseResult.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {parseResult.errors && parseResult.errors.length > 0 && (
            <div className="mt-2 text-sm text-red-700">
              <p className="font-medium">Errors:</p>
              <ul className="list-disc list-inside">
                {parseResult.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderWorkflowStatus = () => {
    if (!workflowStatus) return null;

    const { status, workflow_progress, recommended_next_steps } = workflowStatus;

    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Workflow Progress</h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{status.documents}</div>
            <div className="text-sm text-gray-500">Documents</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{status.claims_total}</div>
            <div className="text-sm text-gray-500">Claims Extracted</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{status.timeline_events}</div>
            <div className="text-sm text-gray-500">Timeline Events</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{status.contradictions_analyzed}</div>
            <div className="text-sm text-gray-500">Contradictions</div>
          </div>
        </div>

        <div className="flex gap-2 mb-4">
          {Object.entries(workflow_progress).map(([key, completed]) => (
            <span
              key={key}
              className={`px-2 py-1 text-xs rounded-full ${
                completed ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
              }`}
            >
              {key.replace(/_/g, ' ')}
            </span>
          ))}
        </div>

        {recommended_next_steps.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Recommended Next:</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              {recommended_next_steps.slice(0, 3).map((step, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="w-5 h-5 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs">
                    {step.priority}
                  </span>
                  {step.action}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  if (!caseId) {
    return (
      <div className="p-6">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-amber-800">No Case Selected</h2>
          <p className="text-amber-700">
            Please select a case to use the AI workflow.{' '}
            <Link to="/cases" className="underline">
              Go to Cases
            </Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Subscription Workflow</h1>
        <p className="text-gray-600">
          Generate prompts for your AI subscriptions and import the results
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
          <button onClick={() => setError('')} className="float-right text-red-500 hover:text-red-700">
            Dismiss
          </button>
        </div>
      )}

      {renderWorkflowStatus()}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('generate')}
            className={`flex-1 py-3 px-4 text-center font-medium ${
              activeTab === 'generate'
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-700'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Generate Prompt
          </button>
          <button
            onClick={() => setActiveTab('import')}
            className={`flex-1 py-3 px-4 text-center font-medium ${
              activeTab === 'import'
                ? 'bg-green-50 text-green-700 border-b-2 border-green-700'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Import Response
          </button>
        </div>

        <div className="p-6">
          {activeTab === 'generate' && (
            <>
              {renderPromptTypeSelector()}
              {renderGeneratedPrompt()}
            </>
          )}
          {activeTab === 'import' && renderImportTab()}
        </div>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-medium text-gray-900 mb-2">Supported Platforms</h3>
        <div className="flex flex-wrap gap-2">
          {['Claude', 'ChatGPT', 'Grok', 'Perplexity', 'Le Chat', 'Venice AI'].map((platform) => (
            <span key={platform} className="px-3 py-1 bg-white border border-gray-200 rounded-full text-sm">
              {platform}
            </span>
          ))}
        </div>
        <p className="mt-3 text-sm text-gray-600">
          This workflow is designed for copy-paste use with your AI subscription platforms, avoiding API
          costs while leveraging full AI capabilities.
        </p>
      </div>
    </div>
  );
}
