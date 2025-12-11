# PHRONESIS HANDOFF: QUICK REFERENCE

## FOR PAUL (YOU)

**What I've built for you:**
1. **Strategic Framework** - Violation-first methodology
2. **Technical Specification** - Complete architecture for Claude Code
3. **Evidence Tracker** - Honest assessment of what we have vs need
4. **Implementation Prompt** - Ready to copy-paste to terminal agent

**Next Action:**
Copy the implementation prompt (Part 8 of CLAUDE_CODE_IMPLEMENTATION_SPEC.md) and give it to your Claude Code terminal agent.

---

## FOR CLAUDE CODE (TERMINAL AGENT)

**Your Job:**
Build the documentary analysis pipeline in Python.

**Priority 1 (Start Here):**
- Parse transcript JSON
- Count references (Paul, Samantha, suspect, etc.)
- Classify segments (accusatory, suspect-framing, exculpatory)
- Calculate metrics (27:1 ratio, 45:43 delay)
- Generate Markdown report

**Input:**
`/mnt/project/12-08_Vendetta_Part_One__Cambridgeshire_Double_Murder_Investigation.json`

**Output:**
Professional analysis report showing:
- Reference counts by type
- Segment classifications
- Timing analysis
- Evidence gap identification

**Success:**
- 27+ suspect-framing references detected
- ~1 exculpatory reference (in trailer)
- First exculpatory at 00:45:43
- Clean, extensible code structure

---

## KEY FILES

| File | Purpose | For |
|------|---------|-----|
| CLAUDE_CODE_IMPLEMENTATION_SPEC.md | Complete technical spec | Claude Code |
| PHRONESIS_VIOLATIONS_ANALYSIS.md | 12 violations with evidence needs | Both |
| PHRONESIS_EVIDENCE_TRACKER.md | What we have vs need | Paul |

---

## THE WORKFLOW

```
PAUL (You) → Give spec to Claude Code
                  ↓
         CLAUDE CODE → Builds the system
                  ↓
              System → Analyzes transcripts
                  ↓
             Output → Violation reports with evidence gaps
                  ↓
PAUL (You) → Reviews reports, provides requested evidence
                  ↓
         CLAUDE CODE → Refines analysis with new evidence
                  ↓
              Final → Complete complaint packages
```

---

## PHILOSOPHY REMINDER

**Lean & Honest:**
- Start with violations
- Request evidence only when needed
- Assess strength honestly (STRONG/MODERATE/WEAK/UNSUBSTANTIATED)
- Flag gaps explicitly

**No Noise:**
- Don't process 2000 pages hoping to find something
- Process only what's needed to prove specific violations
- Request documents by name when needed for specific claims

---

*Handoff Package Complete*
*Date: 10 December 2025*
