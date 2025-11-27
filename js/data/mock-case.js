// Mock Case Data - PE23C50095
const mockData = {
    case: {
        id: 'PE23C50095',
        reference: 'PE23C50095',
        title: 'Suffolk CC v Stephen & Dunmore',
        status: 'active',
        createdAt: '2023-06-09',
        court: 'Family Court (Ipswich)',
        judge: 'HHJ Gordon-Saker',
        relatedCases: ['PE22P31058', 'PE23P30344', 'PE21P30644']
    },
    subjects: [
        {
            id: 1,
            name: 'Dr. Emma Hunnisett',
            role: 'CafCass Family Court Advisor',
            isPrimary: true,
            riskScore: 78,
            riskLevel: 'High',
            status: 'Under Review',
            profile: {
                position: 'Family Court Advisor',
                organization: 'CafCass',
                qualifications: 'Section 7 Report Author',
                yearsActive: 'Unknown'
            },
            flags: ['Report Methodology Questions', 'Assessment Protocol Concerns', 'Timeline Discrepancies']
        },
        { id: 2, name: 'Suffolk County Council', role: 'Local Authority Applicant', isPrimary: false, riskScore: 52, riskLevel: 'Medium', status: 'Active Party' },
        { id: 3, name: 'Samantha Stephen', role: 'Mother / First Respondent', isPrimary: false, riskScore: 15, riskLevel: 'Low', status: 'Respondent' },
        { id: 4, name: 'Paul Stephen', role: 'Step-Father / Second Respondent', isPrimary: false, riskScore: 15, riskLevel: 'Low', status: 'Respondent' },
        { id: 5, name: 'Josh Dunmore', role: 'Father / Third Respondent', isPrimary: false, riskScore: 20, riskLevel: 'Low', status: 'Respondent' },
        { id: 6, name: 'Mandy Seamark', role: 'Paternal Grandmother', isPrimary: false, riskScore: 25, riskLevel: 'Low', status: 'Intervenor' },
        { id: 7, name: 'Ryan Dunmore', role: 'Child (Subject)', isPrimary: false, riskScore: 0, riskLevel: 'Protected', status: 'Subject Child - ASD' },
        { id: 8, name: 'Freya Stephen', role: 'Child (Subject)', isPrimary: false, riskScore: 0, riskLevel: 'Protected', status: 'Subject Child - Foster Care' }
    ],
    entities: [
        { id: 1, name: 'CafCass', type: 'organization', connectionStrength: 95 },
        { id: 2, name: 'Family Court Ipswich', type: 'institution', connectionStrength: 100 },
        { id: 3, name: 'Suffolk County Council', type: 'organization', connectionStrength: 90 },
        { id: 4, name: 'RAF Lakenheath', type: 'organization', connectionStrength: 45 },
        { id: 5, name: 'Suffolk Police', type: 'organization', connectionStrength: 70 },
        { id: 6, name: 'Guardian (Lucy Ardern)', type: 'individual', connectionStrength: 65 }
    ],
    violations: [
        { id: 'V-001', code: 'CW-1.1', title: 'Child welfare - Sibling separation without assessment', severity: 'critical', status: 'confirmed', date: '2023-06-09', subject: 'Local Authority', evidence: 5 },
        { id: 'V-002', code: 'PR-2.1', title: 'Procedural - ICO granted without full hearing', severity: 'high', status: 'under_review', date: '2023-06-09', subject: 'Court Process', evidence: 3 },
        { id: 'V-003', code: 'AS-1.2', title: 'Assessment methodology concerns in Section 7', severity: 'high', status: 'investigating', date: '2022-09-28', subject: 'Dr. Emma Hunnisett', evidence: 4 },
        { id: 'V-004', code: 'TL-1.3', title: 'Timeline inconsistencies in witness statements', severity: 'high', status: 'confirmed', date: '2024-02-26', subject: 'Multiple Parties', evidence: 6 },
        { id: 'V-005', code: 'CM-2.1', title: 'Communication failures between agencies', severity: 'medium', status: 'investigating', date: '2023-08-01', subject: 'Local Authority', evidence: 3 },
        { id: 'V-006', code: 'CT-1.1', title: 'Contact arrangements inadequate for child needs', severity: 'medium', status: 'under_review', date: '2023-12-15', subject: 'Local Authority', evidence: 2 },
        { id: 'V-007', code: 'DP-1.2', title: 'Disclosure delays - Police materials', severity: 'medium', status: 'confirmed', date: '2023-06-19', subject: 'Suffolk Police', evidence: 2 },
        { id: 'V-008', code: 'FF-1.1', title: 'Fact-finding hearing concerns', severity: 'high', status: 'under_review', date: '2024-03-15', subject: 'Court Process', evidence: 4 }
    ],
    tasks: [
        { id: 1, title: 'Analyze Section 7 Report methodology', description: 'Review Dr. Hunnisett assessment process and conclusions', status: 'completed', priority: 'high', assignee: 'Legal' },
        { id: 2, title: 'Cross-reference police disclosure', description: 'Compare police materials with LA statements', status: 'completed', priority: 'high', assignee: 'Analyst' },
        { id: 3, title: 'Verify interview transcripts', description: 'Check AI transcriptions against audio recordings', status: 'in_progress', priority: 'high', assignee: 'Analyst' },
        { id: 4, title: 'Map entity relationships', description: 'Document connections between all parties and agencies', status: 'in_progress', priority: 'medium', assignee: 'Analyst' },
        { id: 5, title: 'Compile contact notes analysis', description: 'Review supervised contact observations', status: 'todo', priority: 'medium', assignee: 'Analyst' },
        { id: 6, title: 'Timeline reconstruction', description: 'Build comprehensive event chronology 2021-2024', status: 'todo', priority: 'high', assignee: 'Legal' },
        { id: 7, title: 'Appeal grounds preparation', description: 'Document basis for appeal of March 2024 judgment', status: 'review', priority: 'high', assignee: 'Legal' },
        { id: 8, title: 'Child welfare impact assessment', description: 'Document effects of separation on Ryan and Freya', status: 'todo', priority: 'high', assignee: 'Expert' }
    ],
    timeline: [
        { id: 1, date: '2021-09-17', title: 'Private Law Proceedings Begin', description: 'Initial CAO application filed (PE21P30644)', type: 'milestone', isAnomaly: false },
        { id: 2, date: '2022-02-01', title: 'Further Proceedings', description: 'PE22P31058 proceedings initiated', type: 'milestone', isAnomaly: false },
        { id: 3, date: '2022-09-28', title: 'Section 7 Report Filed', description: 'CafCass report by Dr. Hunnisett submitted', type: 'document', isAnomaly: false },
        { id: 4, date: '2022-11-01', title: 'CafCass Addendum', description: 'Additional CafCass assessment provided', type: 'document', isAnomaly: false },
        { id: 5, date: '2023-06-09', title: 'Emergency ICO Hearing', description: 'HHJ Gordon-Saker grants Interim Care Order', type: 'milestone', isAnomaly: true, anomalyType: 'Procedural Concern' },
        { id: 6, date: '2023-06-09', title: 'Children Removed', description: 'Ryan placed with PGM, Freya to foster care', type: 'violation', isAnomaly: true, anomalyType: 'Sibling Separation' },
        { id: 7, date: '2023-06-19', title: 'Police Disclosure Order', description: 'Court orders police disclosure', type: 'order', isAnomaly: false },
        { id: 8, date: '2023-10-05', title: 'CMH Hearing', description: 'Case Management Hearing', type: 'hearing', isAnomaly: false },
        { id: 9, date: '2023-10-27', title: 'Directions Hearing', description: 'Further directions given', type: 'hearing', isAnomaly: false },
        { id: 10, date: '2023-12-15', title: 'IRH Hearing', description: 'Issues Resolution Hearing', type: 'hearing', isAnomaly: false },
        { id: 11, date: '2024-02-09', title: 'Pre-Trial Review', description: 'PTR before fact-finding', type: 'hearing', isAnomaly: false },
        { id: 12, date: '2024-02-26', title: 'Fact-Finding Begins', description: '5-day fact-finding hearing commences', type: 'milestone', isAnomaly: false },
        { id: 13, date: '2024-03-15', title: 'Judgment Delivered', description: 'Findings of fact delivered', type: 'milestone', isAnomaly: true, anomalyType: 'Appeal Pending' },
        { id: 14, date: '2024-04-19', title: 'Post-Judgment Hearing', description: 'Welfare stage directions', type: 'hearing', isAnomaly: false },
        { id: 15, date: '2024-07-19', title: 'Court Order', description: 'Further orders made', type: 'order', isAnomaly: false },
        { id: 16, date: '2024-09-26', title: 'Review Hearing', description: 'Case review hearing', type: 'hearing', isAnomaly: false },
        { id: 17, date: '2024-10-09', title: 'Directions Hearing', description: 'Further case management', type: 'hearing', isAnomaly: false }
    ],
    documents: [
        { id: 1, name: 'A - Preliminary Documents', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 2, name: 'B - Applications & Orders', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 3, name: 'C - Statements & Affidavits', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 4, name: 'D - Care Plans', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 5, name: 'E - Expert Reports', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 6, name: 'F - Miscellaneous', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 7, name: 'G - Police Disclosure', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 8, name: 'H - Previous Proceedings PE22P31058', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 9, name: 'I - Private Law PE23P30344', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 10, name: 'J - Private Law PE21P30644', type: 'bundle', status: 'analyzed', date: '2024-01-17' },
        { id: 11, name: 'Section 7 Report (28 Sept 2022)', type: 'report', status: 'analyzed', date: '2022-09-28' },
        { id: 12, name: 'CafCass Letter 17 Sept 2021', type: 'correspondence', status: 'analyzed', date: '2021-09-17' },
        { id: 13, name: 'CafCass Letter 08 Apr 2022', type: 'correspondence', status: 'analyzed', date: '2022-04-08' },
        { id: 14, name: 'CafCass 18 May 2022', type: 'correspondence', status: 'analyzed', date: '2022-05-18' },
        { id: 15, name: 'CafCass 1 November 2022', type: 'correspondence', status: 'analyzed', date: '2022-11-01' },
        { id: 16, name: 'Paul Stephen Interview Part 1', type: 'audio', status: 'transcribed', date: '2025-03-26' },
        { id: 17, name: 'Paul Stephen Interview Part 2', type: 'audio', status: 'transcribed', date: '2025-03-26' },
        { id: 18, name: 'Paul Stephen Interview Part 3', type: 'audio', status: 'transcribed', date: '2025-03-26' },
        { id: 19, name: 'Paul Stephen Interview Part 4', type: 'audio', status: 'transcribed', date: '2025-03-26' },
        { id: 20, name: 'Samantha Stephen Interview Part 1', type: 'audio', status: 'transcribed', date: '2025-05-03' },
        { id: 21, name: 'Samantha Stephen Interview Part 2', type: 'audio', status: 'transcribed', date: '2025-05-03' },
        { id: 22, name: 'Court Order 9 June 2023 (ICO)', type: 'order', status: 'analyzed', date: '2023-06-09' },
        { id: 23, name: 'Police Disclosure Order 19 June 2023', type: 'order', status: 'analyzed', date: '2023-06-19' },
        { id: 24, name: 'Court Order 19 April 2024', type: 'order', status: 'analyzed', date: '2024-04-19' },
        { id: 25, name: 'Court Order 19 July 2024', type: 'order', status: 'analyzed', date: '2024-07-19' },
        { id: 26, name: 'Supervised Contact Notes (Monthly)', type: 'notes', status: 'analyzed', date: '2024-08-14' },
        { id: 27, name: 'Mandy Seamark Statement', type: 'statement', status: 'analyzed', date: '2024-05-08' },
        { id: 28, name: 'PGM Grounds of Appeal Response', type: 'statement', status: 'analyzed', date: '2024-05-01' }
    ],
    getFullCase() {
        return {
            case: this.case,
            subjects: this.subjects,
            violations: this.violations,
            timeline: this.timeline,
            tasks: this.tasks,
            documents: this.documents,
            entities: this.entities
        };
    }
};

// API Service
const api = {
    baseUrl: '',
    async getMockData(endpoint) {
        await new Promise(resolve => setTimeout(resolve, 300));
        if (endpoint.includes('/cases/') && endpoint.endsWith('/full')) return mockData.getFullCase();
        return null;
    },
    async getCase(caseId) {
        return this.getMockData(`/cases/${caseId}/full`);
    }
};
