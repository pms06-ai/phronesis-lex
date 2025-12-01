"""
FCIP v5.0 Temporal Logic Engine

Features:
- Natural language temporal parsing
- Allen's interval algebra for temporal relations
- UK court calendar (working days, bank holidays)
- Deadline calculation and alerting
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Optional, Set, Tuple

try:
    import parsedatetime
    PARSEDATETIME_AVAILABLE = True
except ImportError:
    PARSEDATETIME_AVAILABLE = False

try:
    from dateutil import parser as dateutil_parser
    from dateutil.relativedelta import relativedelta
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

from ..models.core import ParsedTemporal


# =============================================================================
# TEMPORAL RELATIONS (Allen's Interval Algebra)
# =============================================================================

class TemporalRelation(str, Enum):
    """Allen's interval algebra relations."""
    BEFORE = "before"           # A ends before B starts
    AFTER = "after"             # A starts after B ends
    MEETS = "meets"             # A ends exactly when B starts
    MET_BY = "met_by"           # A starts exactly when B ends
    OVERLAPS = "overlaps"       # A starts before B, A ends during B
    OVERLAPPED_BY = "overlapped_by"
    DURING = "during"           # A is contained within B
    CONTAINS = "contains"       # A contains B
    STARTS = "starts"           # A and B start together, A ends first
    STARTED_BY = "started_by"
    FINISHES = "finishes"       # A and B end together, A starts after B
    FINISHED_BY = "finished_by"
    EQUALS = "equals"           # A and B are identical


# =============================================================================
# DEADLINE PATTERNS
# =============================================================================

DEADLINE_PATTERNS = [
    # "within X days/weeks/months of Y"
    (r"within\s+(\d+)\s+(day|week|month)s?\s+(?:of|from)\s+(.+)", "relative"),
    # "by 15th March 2024"
    (r"by\s+(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})", "absolute"),
    # "X days from the date of this order"
    (r"(\d+)\s+(day|week)s?\s+from\s+(?:the\s+)?date\s+of", "from_date"),
    # "no later than X"
    (r"no\s+later\s+than\s+(.+)", "absolute"),
    # "forthwith" / "immediately"
    (r"\bforthwith\b", "immediate"),
    (r"\bimmediately\b", "immediate"),
    # "before the next hearing"
    (r"before\s+(?:the\s+)?(?:next\s+)?hearing", "before_hearing"),
    # Working days pattern
    (r"(\d+)\s+(?:clear\s+)?working\s+days?", "working_days"),
]


# =============================================================================
# UK BANK HOLIDAYS (2024-2025)
# =============================================================================

UK_BANK_HOLIDAYS_2024 = {
    date(2024, 1, 1),    # New Year's Day
    date(2024, 3, 29),   # Good Friday
    date(2024, 4, 1),    # Easter Monday
    date(2024, 5, 6),    # Early May Bank Holiday
    date(2024, 5, 27),   # Spring Bank Holiday
    date(2024, 8, 26),   # Summer Bank Holiday
    date(2024, 12, 25),  # Christmas Day
    date(2024, 12, 26),  # Boxing Day
}

UK_BANK_HOLIDAYS_2025 = {
    date(2025, 1, 1),    # New Year's Day
    date(2025, 4, 18),   # Good Friday
    date(2025, 4, 21),   # Easter Monday
    date(2025, 5, 5),    # Early May Bank Holiday
    date(2025, 5, 26),   # Spring Bank Holiday
    date(2025, 8, 25),   # Summer Bank Holiday
    date(2025, 12, 25),  # Christmas Day
    date(2025, 12, 26),  # Boxing Day
}


@dataclass
class CourtCalendar:
    """UK court calendar with bank holidays and working day calculation."""
    bank_holidays: Set[date] = field(default_factory=lambda: UK_BANK_HOLIDAYS_2024 | UK_BANK_HOLIDAYS_2025)

    def is_working_day(self, d: date) -> bool:
        """Check if date is a working day (not weekend or bank holiday)."""
        return d.weekday() < 5 and d not in self.bank_holidays

    def add_working_days(self, start: date, days: int) -> date:
        """Add working days to a start date."""
        result = start
        remaining = abs(days)
        direction = 1 if days >= 0 else -1

        while remaining > 0:
            result += timedelta(days=direction)
            if self.is_working_day(result):
                remaining -= 1

        return result

    def working_days_between(self, start: date, end: date) -> int:
        """Count working days between two dates."""
        if start > end:
            start, end = end, start

        count = 0
        current = start
        while current <= end:
            if self.is_working_day(current):
                count += 1
            current += timedelta(days=1)
        return count

    def next_working_day(self, d: date) -> date:
        """Get the next working day on or after the given date."""
        while not self.is_working_day(d):
            d += timedelta(days=1)
        return d


@dataclass
class TemporalInterval:
    """A temporal interval with start and end points."""
    start: Optional[date] = None
    end: Optional[date] = None
    precision: str = "unknown"  # day, month, year, unknown

    def overlaps(self, other: "TemporalInterval") -> bool:
        """Check if this interval overlaps with another."""
        if self.start is None or self.end is None:
            return False
        if other.start is None or other.end is None:
            return False
        return self.start <= other.end and other.start <= self.end

    def get_relation(self, other: "TemporalInterval") -> Optional[TemporalRelation]:
        """Get Allen's interval relation to another interval."""
        if self.start is None or self.end is None or other.start is None or other.end is None:
            return None

        if self.end < other.start:
            return TemporalRelation.BEFORE
        if self.start > other.end:
            return TemporalRelation.AFTER
        if self.end == other.start:
            return TemporalRelation.MEETS
        if self.start == other.end:
            return TemporalRelation.MET_BY
        if self.start == other.start and self.end == other.end:
            return TemporalRelation.EQUALS
        if self.start <= other.start and self.end >= other.end:
            return TemporalRelation.CONTAINS
        if self.start >= other.start and self.end <= other.end:
            return TemporalRelation.DURING
        if self.start < other.start < self.end < other.end:
            return TemporalRelation.OVERLAPS
        if other.start < self.start < other.end < self.end:
            return TemporalRelation.OVERLAPPED_BY

        return None


class TemporalParser:
    """Parser for temporal expressions in legal documents."""

    def __init__(self, calendar: Optional[CourtCalendar] = None):
        self.calendar = calendar or CourtCalendar()
        self._patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in DEADLINE_PATTERNS]
        if PARSEDATETIME_AVAILABLE:
            self.pdt = parsedatetime.Calendar()
        else:
            self.pdt = None

    def parse(self, text: str, reference_date: Optional[date] = None) -> Optional[ParsedTemporal]:
        """
        Parse a temporal expression.

        Args:
            text: The temporal expression to parse
            reference_date: Reference date for relative expressions

        Returns:
            ParsedTemporal or None if unparseable
        """
        text = text.strip()
        reference_date = reference_date or date.today()

        # Try absolute date parsing first
        parsed_date = self._parse_absolute_date(text)
        if parsed_date:
            return ParsedTemporal(
                raw_text=text,
                expression_type="absolute",
                base_date=parsed_date,
                confidence=0.95
            )

        # Try pattern matching
        for pattern, ptype in self._patterns:
            match = pattern.search(text)
            if match:
                return self._process_pattern_match(text, match, ptype, reference_date)

        # Try parsedatetime for natural language
        if self.pdt:
            try:
                time_struct, parse_status = self.pdt.parse(text)
                if parse_status > 0:
                    parsed_date = date(time_struct.tm_year, time_struct.tm_mon, time_struct.tm_mday)
                    return ParsedTemporal(
                        raw_text=text,
                        expression_type="natural",
                        base_date=parsed_date,
                        confidence=0.7
                    )
            except Exception:
                pass

        return None

    def _parse_absolute_date(self, text: str) -> Optional[date]:
        """Try to parse an absolute date."""
        if not DATEUTIL_AVAILABLE:
            return None

        try:
            # UK date format (day first)
            parsed = dateutil_parser.parse(text, dayfirst=True)
            return parsed.date()
        except Exception:
            return None

    def _process_pattern_match(
        self,
        text: str,
        match: re.Match,
        ptype: str,
        reference_date: date
    ) -> ParsedTemporal:
        """Process a regex pattern match."""

        if ptype == "relative":
            # "within X days/weeks/months of Y"
            value = int(match.group(1))
            unit = match.group(2)
            anchor = match.group(3)
            return ParsedTemporal(
                raw_text=text,
                expression_type="relative",
                offset_value=value,
                offset_unit=unit,
                anchor_event=anchor,
                confidence=0.9,
                is_deadline=True
            )

        elif ptype == "absolute":
            # "by 15th March 2024"
            date_text = match.group(1)
            parsed_date = self._parse_absolute_date(date_text)
            return ParsedTemporal(
                raw_text=text,
                expression_type="absolute",
                base_date=parsed_date,
                confidence=0.9 if parsed_date else 0.5,
                is_deadline=True
            )

        elif ptype == "from_date":
            # "X days from the date of this order"
            value = int(match.group(1))
            unit = match.group(2)
            return ParsedTemporal(
                raw_text=text,
                expression_type="from_date",
                offset_value=value,
                offset_unit=unit,
                anchor_event="date of order",
                confidence=0.85,
                is_deadline=True
            )

        elif ptype == "immediate":
            return ParsedTemporal(
                raw_text=text,
                expression_type="immediate",
                offset_value=0,
                base_date=reference_date,
                confidence=0.95,
                is_deadline=True
            )

        elif ptype == "working_days":
            value = int(match.group(1))
            return ParsedTemporal(
                raw_text=text,
                expression_type="working_days",
                offset_value=value,
                offset_unit="working_day",
                confidence=0.9,
                is_deadline=True,
                working_days=True
            )

        else:
            return ParsedTemporal(
                raw_text=text,
                expression_type=ptype,
                confidence=0.6
            )

    def calculate_deadline(
        self,
        parsed: ParsedTemporal,
        anchor_date: Optional[date] = None
    ) -> Optional[date]:
        """
        Calculate the actual deadline date from a parsed temporal.

        Args:
            parsed: The parsed temporal expression
            anchor_date: The anchor date for relative expressions

        Returns:
            The calculated deadline date
        """
        if parsed.base_date:
            return parsed.base_date

        anchor = anchor_date or date.today()

        if parsed.offset_value is not None and parsed.offset_unit:
            if parsed.working_days:
                return self.calendar.add_working_days(anchor, parsed.offset_value)

            if parsed.offset_unit == "day":
                return anchor + timedelta(days=parsed.offset_value)
            elif parsed.offset_unit == "week":
                return anchor + timedelta(weeks=parsed.offset_value)
            elif parsed.offset_unit == "month":
                if DATEUTIL_AVAILABLE:
                    return anchor + relativedelta(months=parsed.offset_value)
                else:
                    return anchor + timedelta(days=parsed.offset_value * 30)

        return None

    def extract_timeline(self, claims: List[dict]) -> List[dict]:
        """
        Extract temporal events from a list of claims.

        Args:
            claims: List of claim dicts with time_expression fields

        Returns:
            List of timeline events with parsed dates
        """
        events = []
        for claim in claims:
            time_expr = claim.get("time_expression")
            if time_expr:
                parsed = self.parse(time_expr)
                if parsed and parsed.base_date:
                    events.append({
                        "claim_id": claim.get("claim_id"),
                        "date": parsed.base_date.isoformat(),
                        "expression": time_expr,
                        "confidence": parsed.confidence,
                        "is_deadline": parsed.is_deadline
                    })
        return sorted(events, key=lambda x: x["date"])

    def find_temporal_conflicts(
        self,
        events: List[dict]
    ) -> List[Tuple[dict, dict, str]]:
        """
        Find temporal conflicts between events.

        Returns:
            List of (event1, event2, conflict_type) tuples
        """
        conflicts = []
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                # Check for same-day conflicts from different sources
                if event1.get("date") == event2.get("date"):
                    if event1.get("claim_id") != event2.get("claim_id"):
                        conflicts.append((event1, event2, "same_day"))
        return conflicts
