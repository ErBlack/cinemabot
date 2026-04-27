import json
import os
from datetime import datetime

import gspread

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["link", "title", "added_by", "added_at", "current", "watched", "watched_at"]

_worksheet: gspread.Worksheet | None = None


def _get_worksheet() -> gspread.Worksheet:
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        creds_data = json.loads(creds_json)
    else:
        with open("credentials.json") as f:
            creds_data = json.load(f)

    client = gspread.service_account_from_dict(creds_data, scopes=SCOPES)
    spreadsheet = client.open_by_key(os.getenv("SHEET_ID"))

    try:
        _worksheet = spreadsheet.worksheet("films")
    except gspread.WorksheetNotFound:
        _worksheet = spreadsheet.add_worksheet("films", rows=1000, cols=len(HEADERS))
        _worksheet.append_row(HEADERS)

    return _worksheet


def add_film(link: str, title: str, added_by: str) -> bool:
    """Добавляет фильм. Возвращает True если добавлен, False если дубль."""
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(default_blank="")

    for record in records:
        if record.get("link") == link:
            return False

    worksheet.append_row([
        link,
        title,
        added_by,
        datetime.now().isoformat(timespec="seconds"),
        "FALSE",
        "FALSE",
        "",
    ])
    return True


def get_current_film() -> dict | None:
    """Возвращает текущий (выбранный для просмотра) фильм или None."""
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(default_blank="")

    for i, record in enumerate(records):
        if str(record.get("current", "")).upper() == "TRUE":
            return {"row": i + 2, **record}

    return None


def get_unwatched_films() -> list[dict]:
    """Возвращает все непросмотренные и не текущие фильмы."""
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(default_blank="")

    result = []
    for i, record in enumerate(records):
        is_watched = str(record.get("watched", "")).upper() == "TRUE"
        is_current = str(record.get("current", "")).upper() == "TRUE"
        if not is_watched and not is_current:
            result.append({"row": i + 2, **record})

    return result


def set_current_film(row: int) -> None:
    """Помечает фильм как текущий (current = TRUE)."""
    worksheet = _get_worksheet()
    current_col = HEADERS.index("current") + 1
    worksheet.update_cell(row, current_col, "TRUE")


def mark_watched() -> dict | None:
    """Помечает текущий фильм как просмотренный. Возвращает фильм или None."""
    worksheet = _get_worksheet()
    records = worksheet.get_all_records(default_blank="")

    for i, record in enumerate(records):
        if str(record.get("current", "")).upper() == "TRUE":
            row = i + 2
            current_col = HEADERS.index("current") + 1
            watched_col = HEADERS.index("watched") + 1
            watched_at_col = HEADERS.index("watched_at") + 1

            worksheet.update(
                f"R{row}C{current_col}:R{row}C{watched_at_col}",
                [["FALSE", "TRUE", datetime.now().isoformat(timespec="seconds")]],
                value_input_option="USER_ENTERED",
            )

            return record

    return None
