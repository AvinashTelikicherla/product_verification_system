"""CSV processing utilities."""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Tuple


class CSVProcessor:
    """Process CSV files for bulk product ingestion."""

    REQUIRED_COLUMNS = ["wid", "ean", "manufacturing_date", "expiry_date"]

    @staticmethod
    def validate_csv_headers(headers: List[str]) -> Tuple[bool, str]:
        """Validate CSV headers."""
        headers_lower = [h.lower().strip() for h in headers]

        missing = [col for col in CSVProcessor.REQUIRED_COLUMNS if col not in headers_lower]
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}"

        return True, "Valid headers"

    @staticmethod
    def parse_csv_content(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """
        Parse CSV content and return rows, headers, and errors.

        Returns:
            Tuple of (rows, headers, errors)
        """
        rows = []
        headers = []
        errors = []

        try:
            content_str = file_content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(content_str))

            if not reader.fieldnames:
                errors.append("CSV file is empty")
                return rows, headers, errors

            headers = [h.lower().strip() for h in reader.fieldnames]

            # Validate headers
            is_valid, msg = CSVProcessor.validate_csv_headers(headers)
            if not is_valid:
                errors.append(msg)
                return rows, headers, errors

            # Process rows
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    processed_row = CSVProcessor._process_row(row, headers)
                    rows.append(processed_row)
                except ValueError as e:
                    errors.append(f"Row {row_num}: {str(e)}")

        except UnicodeDecodeError:
            errors.append("File encoding error - please use UTF-8 encoding")
        except Exception as e:
            errors.append(f"Error parsing CSV: {str(e)}")

        return rows, headers, errors

    @staticmethod
    def _process_row(row: Dict[str, str], headers: List[str]) -> Dict[str, Any]:
        """Process and validate a single CSV row."""
        processed = {}

        # Map to lowercase for case-insensitive matching
        row_lower = {k.lower().strip(): v.strip() for k, v in row.items()}

        # Required fields
        processed["wid"] = row_lower.get("wid", "").strip()
        processed["ean"] = row_lower.get("ean", "").strip()

        if not processed["wid"]:
            raise ValueError("WID is required")
        if not processed["ean"]:
            raise ValueError("EAN is required")

        # Parse dates
        try:
            mfg_date_str = row_lower.get("manufacturing_date", "").strip()
            exp_date_str = row_lower.get("expiry_date", "").strip()

            processed["manufacturing_date"] = CSVProcessor._parse_date(mfg_date_str)
            processed["expiry_date"] = CSVProcessor._parse_date(exp_date_str)
        except ValueError as e:
            raise ValueError(f"Date parsing error: {str(e)}")

        # Optional fields
        processed["batch_id"] = row_lower.get("batch_id", None) or None
        processed["quantity"] = int(row_lower.get("quantity", 1))
        processed["location"] = row_lower.get("location", None) or None

        return processed

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse date string in multiple formats."""
        if not date_str:
            raise ValueError("Date string is empty")

        # Month-first (US) variants are tried before day-first so that
        # ambiguous slash dates (e.g. 9/2/2025) resolve as month/day.
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Could not parse date: {date_str}")
