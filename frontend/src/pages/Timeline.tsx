/**
 * Timeline Page - Phronesis LEX
 */
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { timelineApi } from '../services/api';
import type { TimelineEvent } from '../types';

const SignificanceBadge = ({ significance }: { significance: string }) => {
  const classes: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-300 border-red-500/30',
    major: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    routine: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
    minor: 'bg-slate-600/20 text-slate-400 border-slate-600/30',
  };

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${classes[significance] || classes.routine}`}>
      {significance}
    </span>
  );
};

const TimelineCard = ({ event, isLast }: { event: TimelineEvent; isLast: boolean }) => {
  return (
    <div className="flex gap-4">
      {/* Timeline line */}
      <div className="flex flex-col items-center">
        <div
          className={`w-4 h-4 rounded-full border-2 ${
            event.significance === 'critical'
              ? 'bg-red-500 border-red-400'
              : event.significance === 'major'
              ? 'bg-amber-500 border-amber-400'
              : 'bg-slate-600 border-slate-500'
          }`}
        />
        {!isLast && <div className="w-0.5 flex-1 bg-slate-700 -mb-4" />}
      </div>

      {/* Content */}
      <div className="card p-4 flex-1 mb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="text-sm font-semibold text-white">
                {new Date(event.event_date).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric'
                })}
              </span>
              <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                {event.event_type}
              </span>
              <SignificanceBadge significance={event.significance} />
              {event.verified && (
                <span className="text-xs text-emerald-400">✓ Verified</span>
              )}
              {event.conflicting_events.length > 0 && (
                <span className="text-xs text-red-400">⚠️ Conflict</span>
              )}
            </div>
            <p className="text-slate-300">{event.description}</p>
            
            {/* Metadata */}
            <div className="flex flex-wrap gap-4 mt-3 text-xs text-slate-500">
              {event.participants.length > 0 && (
                <span>Participants: {event.participants.join(', ')}</span>
              )}
              {event.location && <span>📍 {event.location}</span>}
              <span>Source: {event.source_document_name}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export function Timeline() {
  const { id: caseId } = useParams<{ id: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ['timeline', caseId],
    queryFn: () => timelineApi.forCase(caseId!),
    enabled: !!caseId,
  });

  const { data: conflicts } = useQuery({
    queryKey: ['timeline-conflicts', caseId],
    queryFn: () => timelineApi.getConflicts(caseId!),
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
        <h1 className="text-2xl font-bold text-white">Timeline</h1>
        <p className="text-slate-400 mt-1">
          Chronological events extracted from case documents
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-white">{data?.count || 0}</p>
          <p className="text-xs text-slate-500">Total Events</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-red-400">
            {data?.results.filter(e => e.significance === 'critical').length || 0}
          </p>
          <p className="text-xs text-slate-500">Critical</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-emerald-400">
            {data?.results.filter(e => e.verified).length || 0}
          </p>
          <p className="text-xs text-slate-500">Verified</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-amber-400">
            {conflicts?.conflicts?.length || 0}
          </p>
          <p className="text-xs text-slate-500">Conflicts</p>
        </div>
      </div>

      {/* Conflicts Warning */}
      {conflicts?.conflicts?.length > 0 && (
        <div className="card p-4 bg-amber-500/10 border-amber-500/30">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-amber-400">⚠️</span>
            <h3 className="font-semibold text-amber-300">Timeline Conflicts Detected</h3>
          </div>
          <p className="text-sm text-slate-300">
            {conflicts.conflicts.length} conflicting event(s) found. Review the timeline for inconsistencies.
          </p>
        </div>
      )}

      {/* Timeline */}
      <div className="card p-6">
        {data?.results && data.results.length > 0 ? (
          <div className="pl-2">
            {data.results.map((event, index) => (
              <TimelineCard
                key={event.id}
                event={event}
                isLast={index === data.results.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">📅</div>
            <p className="text-slate-400">No timeline events extracted yet</p>
            <p className="text-sm text-slate-500 mt-1">
              Analyze documents to extract chronological events
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

