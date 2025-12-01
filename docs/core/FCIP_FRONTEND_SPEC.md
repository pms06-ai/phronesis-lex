# FCIP Frontend Implementation Specification

This document specifies the React frontend components needed to integrate with the FCIP (Forensic Case Intelligence Platform) backend engine.

## Overview

The FCIP backend has been integrated into Phronesis LEX at `backend/fcip/`. The frontend needs new components to visualize:
- Statistical bias detection with z-scores
- Toulmin argument structures
- Entity resolution graphs
- Deadline alerts
- Legal rules reference

## API Endpoints Available

### Core FCIP Analysis
```
POST /api/fcip/analyze/{doc_id}
```
Runs full FCIP analysis on a document. Returns:
```json
{
  "status": "completed",
  "doc_type": "section_7_report",
  "doc_type_confidence": 0.95,
  "results": {
    "claims_extracted": 45,
    "entities_found": 12,
    "timeline_events": 8,
    "bias_signals": 3
  },
  "extraction_prompt_hash": "abc123..."
}
```

### Bias Report
```
GET /api/cases/{case_id}/bias-report
```
Returns comprehensive statistical bias analysis:
```json
{
  "case_id": "uuid",
  "total_signals": 15,
  "by_severity": {"high": 2, "medium": 8, "low": 5},
  "by_type": {"certainty_language": 5, "negative_attribution": 7, "quantifier_extremity": 3},
  "statistical_summary": {
    "mean_z_score": 1.8,
    "max_z_score": 2.7,
    "signals_above_critical": 2,
    "signals_above_warning": 8
  },
  "signals": [
    {
      "id": "uuid",
      "type": "certainty_language",
      "severity": "high",
      "z_score": 2.7,
      "p_value": 0.007,
      "direction": "higher",
      "description": "Certainty language is higher than typical...",
      "document_id": "uuid"
    }
  ]
}
```

### Entity Graph
```
GET /api/cases/{case_id}/entity-graph
```
Returns resolved entities with aliases:
```json
{
  "case_id": "uuid",
  "nodes": [
    {
      "id": "uuid",
      "name": "Sarah Johnson",
      "profession": "social_worker",
      "capacity": "children_guardian",
      "party": "child",
      "aliases": ["the social worker", "SW Johnson", "Ms Johnson"]
    }
  ],
  "total_entities": 15,
  "total_aliases": 42
}
```

### Toulmin Arguments
```
GET /api/cases/{case_id}/arguments
POST /api/cases/{case_id}/generate-arguments?finding_type=welfare
```
Returns Toulmin argument structures:
```json
{
  "argument_id": "uuid",
  "argument": {
    "claim": "Based on analysis of 45 claims regarding welfare...",
    "grounds": ["Evidence point 1", "Evidence point 2"],
    "warrant": "Under Paramountcy Principle: The child's welfare...",
    "warrant_rule_id": "CA1989.s1.1",
    "backing": ["Children Act 1989, Section 1(1)"],
    "qualifier": "probably",
    "rebuttal": ["Unless welfare factors weighed differently"],
    "falsifiability_conditions": [
      {
        "type": "missing_evidence",
        "description": "Documentation exists that contradicts...",
        "test_query": "Search for documents that contradict...",
        "impact": "Would weaken or invalidate the argument",
        "priority": 1
      }
    ],
    "confidence_bounds": {
      "lower": 0.6,
      "mean": 0.72,
      "upper": 0.85
    }
  }
}
```

### Legal Rules
```
GET /api/legal-rules?category=welfare
```
Returns UK legal rules library:
```json
{
  "rules": [
    {
      "rule_id": "CA1989.s1.1",
      "short_name": "Paramountcy Principle",
      "full_citation": "Children Act 1989, Section 1(1)",
      "text": "The child's welfare shall be the court's paramount consideration.",
      "category": "welfare"
    }
  ]
}
```

### Deadline Alerts
```
GET /api/cases/{case_id}/deadline-alerts
```
Returns deadline tracking:
```json
{
  "alerts": [
    {
      "id": "uuid",
      "deadline_text": "within 14 days of this order",
      "deadline_date": "2024-03-15",
      "status": "approaching",
      "days_remaining": 5,
      "source_document_id": "uuid"
    }
  ]
}
```

### Bias Baselines
```
GET /api/bias-baselines
POST /api/bias-baselines
```
Manage statistical baselines for bias detection.

---

## Components to Create

### 1. BiasReport.jsx

**Location:** `Phronesis/frontend/src/components/BiasReport.jsx`

**Purpose:** Display statistical bias analysis with z-score visualization

**Features:**
- Summary cards showing total signals by severity (high/medium/low)
- Bar chart or gauge showing z-score distribution
- Color-coded severity indicators (red=high, yellow=medium, green=low)
- Expandable signal details with:
  - Z-score with visual indicator
  - P-value
  - Direction (higher/lower than baseline)
  - Link to source document
- Filter by signal type (certainty, negativity, extremity)

**UI Suggestions:**
```jsx
// Use Mantine components
import { Card, Badge, Progress, Accordion, Group, Text, Stack } from '@mantine/core';

// Z-score visualization
const ZScoreIndicator = ({ zScore }) => {
  const color = Math.abs(zScore) >= 2.0 ? 'red' : Math.abs(zScore) >= 1.5 ? 'yellow' : 'green';
  return (
    <Group>
      <Progress value={Math.min(Math.abs(zScore) * 33, 100)} color={color} />
      <Text size="sm">z = {zScore.toFixed(2)}</Text>
    </Group>
  );
};
```

### 2. ArgumentViewer.jsx

**Location:** `Phronesis/frontend/src/components/ArgumentViewer.jsx`

**Purpose:** Display Toulmin argument structures

**Features:**
- Visual representation of Toulmin structure:
  ```
  GROUNDS ──────┐
                ├──> CLAIM (with qualifier)
  WARRANT ──────┘
     │
  BACKING

  REBUTTAL (conditions that would invalidate)
  ```
- Confidence bounds visualization (lower-mean-upper range)
- Expandable falsifiability conditions
- Link to relevant legal rule
- Missing evidence warnings
- Alternative explanations section

**UI Suggestions:**
```jsx
// Toulmin structure as connected cards
<Stack>
  <Card shadow="sm">
    <Text weight={700}>Claim</Text>
    <Badge>{qualifier}</Badge>
    <Text>{claim_text}</Text>
    <ConfidenceBounds lower={0.6} mean={0.72} upper={0.85} />
  </Card>

  <Group grow>
    <Card>
      <Text weight={700}>Grounds (Evidence)</Text>
      {grounds.map(g => <Text key={g}>{g}</Text>)}
    </Card>
    <Card>
      <Text weight={700}>Warrant (Reasoning)</Text>
      <Text>{warrant}</Text>
      <Badge variant="outline">{warrant_rule_id}</Badge>
    </Card>
  </Group>

  <Card color="red.1">
    <Text weight={700}>Rebuttal Conditions</Text>
    {rebuttal.map(r => <Text key={r}>• {r}</Text>)}
  </Card>

  <Accordion>
    <Accordion.Item value="falsifiability">
      <Accordion.Control>Falsifiability Tests</Accordion.Control>
      <Accordion.Panel>
        {falsifiability_conditions.map(f => (
          <Card key={f.type}>
            <Badge>{f.priority}</Badge>
            <Text>{f.description}</Text>
            <Text size="sm" color="dimmed">{f.test_query}</Text>
          </Card>
        ))}
      </Accordion.Panel>
    </Accordion.Item>
  </Accordion>
</Stack>
```

### 3. EntityResolutionPanel.jsx

**Location:** `Phronesis/frontend/src/components/EntityResolutionPanel.jsx`

**Purpose:** Display resolved entities and their aliases

**Features:**
- List of entities with profession/capacity badges
- Expandable alias list for each entity
- Party affiliation indicator (applicant/respondent/child/etc.)
- Search/filter by name or role
- Integration with existing EntityGraph component

**UI Suggestions:**
```jsx
<Table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Role</th>
      <th>Party</th>
      <th>Aliases</th>
    </tr>
  </thead>
  <tbody>
    {nodes.map(entity => (
      <tr key={entity.id}>
        <td>{entity.name}</td>
        <td><Badge>{entity.profession}</Badge></td>
        <td><Badge variant="outline">{entity.party}</Badge></td>
        <td>
          {entity.aliases.map(a => (
            <Badge key={a} size="sm" variant="light">{a}</Badge>
          ))}
        </td>
      </tr>
    ))}
  </tbody>
</Table>
```

### 4. DeadlineAlerts.jsx

**Location:** `Phronesis/frontend/src/components/DeadlineAlerts.jsx`

**Purpose:** Display deadline tracking and alerts

**Features:**
- List of deadlines sorted by date
- Status indicators: pending, approaching, overdue, completed
- Days remaining countdown
- Color coding: red=overdue, yellow=approaching (<7 days), green=pending
- Link to source document
- Calendar view option

**UI Suggestions:**
```jsx
const statusColors = {
  overdue: 'red',
  approaching: 'yellow',
  pending: 'blue',
  completed: 'green'
};

<Stack>
  {alerts.map(alert => (
    <Card key={alert.id} withBorder>
      <Group position="apart">
        <Group>
          <Badge color={statusColors[alert.status]}>{alert.status}</Badge>
          <Text>{alert.deadline_text}</Text>
        </Group>
        <Group>
          <Text size="sm" color="dimmed">
            {alert.deadline_date}
          </Text>
          {alert.days_remaining !== null && (
            <Badge variant="outline">
              {alert.days_remaining} days
            </Badge>
          )}
        </Group>
      </Group>
    </Card>
  ))}
</Stack>
```

### 5. LegalRulesReference.jsx

**Location:** `Phronesis/frontend/src/components/LegalRulesReference.jsx`

**Purpose:** Quick reference for UK legal rules

**Features:**
- Searchable list of legal rules
- Filter by category (welfare, threshold, evidence, professional, procedural)
- Expandable full text
- Copy citation button
- Link rules to arguments that use them

**UI Suggestions:**
```jsx
<Stack>
  <SegmentedControl
    data={['All', 'Welfare', 'Threshold', 'Evidence', 'Professional']}
    value={category}
    onChange={setCategory}
  />

  <Accordion>
    {rules.map(rule => (
      <Accordion.Item key={rule.rule_id} value={rule.rule_id}>
        <Accordion.Control>
          <Group>
            <Badge size="sm">{rule.rule_id}</Badge>
            <Text weight={500}>{rule.short_name}</Text>
          </Group>
        </Accordion.Control>
        <Accordion.Panel>
          <Text size="sm" color="dimmed">{rule.full_citation}</Text>
          <Text mt="sm">{rule.text}</Text>
          <Button size="xs" variant="subtle" onClick={() => copy(rule.full_citation)}>
            Copy Citation
          </Button>
        </Accordion.Panel>
      </Accordion.Item>
    ))}
  </Accordion>
</Stack>
```

### 6. FCIPAnalysisButton.jsx

**Location:** `Phronesis/frontend/src/components/FCIPAnalysisButton.jsx`

**Purpose:** Replace/augment existing RunAnalysisButton with FCIP

**Features:**
- Button to trigger FCIP analysis
- Loading state during analysis
- Results summary modal/notification
- Option to choose analysis type

**API Call:**
```javascript
const runFCIPAnalysis = async (docId) => {
  const response = await api.post(`/api/fcip/analyze/${docId}`);
  return response.data;
};
```

---

## Page Updates

### Update: Biases.jsx

Add the new BiasReport component to show statistical analysis alongside existing bias indicators.

```jsx
// Add to existing Biases page
import BiasReport from '../components/BiasReport';

// In the component
const { data: biasReport } = useQuery(
  ['bias-report', caseId],
  () => api.get(`/api/cases/${caseId}/bias-report`).then(r => r.data)
);

// Render BiasReport alongside existing bias list
<Tabs>
  <Tabs.Tab label="Statistical Analysis">
    <BiasReport data={biasReport} />
  </Tabs.Tab>
  <Tabs.Tab label="All Indicators">
    {/* Existing bias indicators list */}
  </Tabs.Tab>
</Tabs>
```

### Update: Entities.jsx

Add EntityResolutionPanel to show resolved entities with aliases.

### New Page: Arguments.jsx

**Location:** `Phronesis/frontend/src/pages/Arguments.jsx`

Create new page to display and generate Toulmin arguments.

```jsx
import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Stack, Button, Select, Card } from '@mantine/core';
import ArgumentViewer from '../components/ArgumentViewer';

export default function Arguments() {
  const { caseId } = useParams();
  const [findingType, setFindingType] = useState('welfare');

  const { data: arguments } = useQuery(
    ['arguments', caseId],
    () => api.get(`/api/cases/${caseId}/arguments`).then(r => r.data)
  );

  const generateMutation = useMutation(
    () => api.post(`/api/cases/${caseId}/generate-arguments?finding_type=${findingType}`)
  );

  return (
    <Stack>
      <Group>
        <Select
          label="Finding Type"
          data={['welfare', 'threshold', 'credibility', 'expert', 'bias']}
          value={findingType}
          onChange={setFindingType}
        />
        <Button onClick={() => generateMutation.mutate()}>
          Generate Argument
        </Button>
      </Group>

      {arguments?.arguments?.map(arg => (
        <ArgumentViewer key={arg.id} argument={arg} />
      ))}
    </Stack>
  );
}
```

### Update: App.jsx Routes

Add new route for Arguments page:
```jsx
<Route path="/cases/:caseId/arguments" element={<Arguments />} />
```

### Update: Layout.jsx Navigation

Add navigation items:
```jsx
{ label: 'Arguments', path: `/cases/${caseId}/arguments`, icon: IconScale },
{ label: 'Deadlines', path: `/cases/${caseId}/deadlines`, icon: IconClock },
```

---

## API Service Updates

**Location:** `Phronesis/frontend/src/services/api.js`

Add new API functions:

```javascript
// FCIP Analysis
export const runFCIPAnalysis = (docId) =>
  api.post(`/api/fcip/analyze/${docId}`);

// Bias Report
export const getBiasReport = (caseId) =>
  api.get(`/api/cases/${caseId}/bias-report`);

// Entity Graph
export const getEntityGraph = (caseId) =>
  api.get(`/api/cases/${caseId}/entity-graph`);

// Arguments
export const getArguments = (caseId) =>
  api.get(`/api/cases/${caseId}/arguments`);

export const generateArguments = (caseId, findingType) =>
  api.post(`/api/cases/${caseId}/generate-arguments?finding_type=${findingType}`);

// Deadlines
export const getDeadlineAlerts = (caseId) =>
  api.get(`/api/cases/${caseId}/deadline-alerts`);

// Legal Rules
export const getLegalRules = (category) =>
  api.get(`/api/legal-rules${category ? `?category=${category}` : ''}`);

// Bias Baselines
export const getBiasBaselines = () =>
  api.get('/api/bias-baselines');
```

---

## Styling Notes

The existing project uses:
- **Mantine UI 8.3.9** - Use Mantine components
- **Tailwind CSS 3.4** - For utility classes
- **Color scheme**: Follows existing dark/light theme

Key colors for FCIP components:
- Critical/High severity: `red`
- Warning/Medium severity: `yellow`
- Normal/Low severity: `green`
- Informational: `blue`

---

## Testing Checklist

After implementation, verify:
- [ ] BiasReport displays z-scores correctly
- [ ] ArgumentViewer shows all Toulmin components
- [ ] EntityResolutionPanel lists all aliases
- [ ] DeadlineAlerts shows correct status colors
- [ ] LegalRulesReference filters work
- [ ] FCIP analysis button triggers analysis
- [ ] New routes accessible from navigation
- [ ] Dark/light theme works on all components

---

## Files Summary

### New Components
- `src/components/BiasReport.jsx`
- `src/components/ArgumentViewer.jsx`
- `src/components/EntityResolutionPanel.jsx`
- `src/components/DeadlineAlerts.jsx`
- `src/components/LegalRulesReference.jsx`
- `src/components/FCIPAnalysisButton.jsx`

### New Pages
- `src/pages/Arguments.jsx`
- `src/pages/Deadlines.jsx` (optional, could be part of Timeline)

### Updated Files
- `src/pages/Biases.jsx` - Add BiasReport tab
- `src/pages/Entities.jsx` - Add EntityResolutionPanel
- `src/services/api.js` - Add FCIP API functions
- `src/App.jsx` - Add new routes
- `src/components/Layout.jsx` - Add navigation items
