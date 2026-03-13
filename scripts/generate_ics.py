import hashlib
import requests
from pathlib import Path
from datetime import datetime

SOURCE_URL = "https://www.officeholidays.com/ics-clean/indonesia"
OUTPUT = Path("docs/indonesia-holidays.ics")

SUMMARY_TRANSLATIONS = {
    "New Year's Day": "Tahun Baru Masehi",
    "Chinese New Year": "Tahun Baru Imlek",
    "Isra and Mi'raj": "Isra Mikraj Nabi Muhammad SAW",
    "Isra and Miraj": "Isra Mikraj Nabi Muhammad SAW",
    "Day of Silence": "Hari Suci Nyepi Tahun Baru Saka",
    "Balinese New Year": "Hari Suci Nyepi Tahun Baru Saka",
    "Good Friday": "Wafat Isa Al Masih",
    "Easter Sunday": "Hari Paskah",
    "Labour Day": "Hari Buruh Internasional",
    "International Labor Day": "Hari Buruh Internasional",
    "Waisak Day": "Hari Raya Waisak",
    "Vesak Day": "Hari Raya Waisak",
    "Ascension Day": "Kenaikan Isa Al Masih",
    "Ascension Day of Jesus Christ": "Kenaikan Isa Al Masih",
    "Pancasila Day": "Hari Lahir Pancasila",
    "Eid al-Fitr": "Hari Raya Idulfitri",
    "Eid ul-Fitr": "Hari Raya Idulfitri",
    "Eid al-Adha": "Hari Raya Iduladha",
    "Eid ul-Adha": "Hari Raya Iduladha",
    "Islamic New Year": "Tahun Baru Islam 1 Muharam",
    "Muharram": "Tahun Baru Islam 1 Muharam",
    "The Prophet Muhammad's Birthday": "Maulid Nabi Muhammad SAW",
    "Prophet Muhammad's Birthday": "Maulid Nabi Muhammad SAW",
    "Independence Day": "Hari Kemerdekaan Republik Indonesia",
    "Christmas Day": "Hari Raya Natal",
}

DESCRIPTION_TRANSLATIONS = {
    "Public Holiday": "Hari Libur Nasional",
    "National Holiday": "Hari Libur Nasional",
    "Holiday": "Hari Libur",
}

def escape_ics_text(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\n")
    )

def unescape_ics_text(text: str) -> str:
    return (
        str(text)
        .replace(r"\n", "\n")
        .replace(r"\,", ",")
        .replace(r"\;", ";")
        .replace("\\\\", "\\")
    )

def fold_ics_line(line: str, limit: int = 75) -> list[str]:
    if len(line) <= limit:
        return [line]

    parts = []
    while len(line) > limit:
        parts.append(line[:limit])
        line = " " + line[limit:]
    parts.append(line)
    return parts

def unfold_ics_lines(text: str) -> list[str]:
    raw_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    unfolded = []

    for line in raw_lines:
        if not unfolded:
            unfolded.append(line)
            continue

        if line.startswith(" ") or line.startswith("\t"):
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)

    return unfolded

def translate_summary(value: str) -> str:
    clean = unescape_ics_text(value).strip()
    return SUMMARY_TRANSLATIONS.get(clean, clean)

def translate_description(value: str) -> str:
    clean = unescape_ics_text(value).strip()
    if clean in DESCRIPTION_TRANSLATIONS:
        return DESCRIPTION_TRANSLATIONS[clean]
    return clean if clean else "Hari Libur Nasional Indonesia"

def parse_events(lines: list[str]) -> list[dict]:
    events = []
    current = None

    for line in lines:
        if line == "BEGIN:VEVENT":
            current = {"raw": []}
            continue

        if line == "END:VEVENT":
            if current:
                events.append(current)
                current = None
            continue

        if current is None:
            continue

        current["raw"].append(line)

        if ":" not in line:
            continue

        key_part, value = line.split(":", 1)
        prop_name = key_part.split(";", 1)[0].upper()

        if prop_name == "DTSTART":
            current["DTSTART_LINE"] = line
            current["DTSTART_VALUE"] = value
        elif prop_name == "DTEND":
            current["DTEND_LINE"] = line
            current["DTEND_VALUE"] = value
        elif prop_name == "SUMMARY":
            current["SUMMARY_VALUE"] = value
        elif prop_name == "DESCRIPTION":
            current["DESCRIPTION_VALUE"] = value

    return events

def make_uid(dtstart_value: str, summary: str) -> str:
    seed = f"{dtstart_value}|{summary}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    return f"{digest}@kalender-libur-indonesia.github.io"

def add_line(lines_out: list[str], line: str):
    for part in fold_ics_line(line):
        lines_out.append(part)

def build_calendar(events: list[dict]) -> str:
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines_out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GitHub Actions//Hari Libur Nasional Indonesia//ID",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Hari Libur Nasional Indonesia",
        "X-WR-TIMEZONE:Asia/Jakarta",
        "X-WR-CALDESC:Kalender hari libur nasional Indonesia terjemahan Bahasa Indonesia dari OfficeHolidays",
    ]

    for event in events:
        dtstart_line = event.get("DTSTART_LINE")
        dtend_line = event.get("DTEND_LINE")

        if not dtstart_line or not dtend_line:
            continue

        summary_id = translate_summary(event.get("SUMMARY_VALUE", "Hari Libur"))
        description_id = translate_description(
            event.get("DESCRIPTION_VALUE", "Hari Libur Nasional Indonesia")
        )

        uid = make_uid(event.get("DTSTART_VALUE", ""), summary_id)

        lines_out.append("BEGIN:VEVENT")
        add_line(lines_out, f"UID:{uid}")
        add_line(lines_out, f"DTSTAMP:{now_utc}")
        add_line(lines_out, f"CREATED:{now_utc}")
        add_line(lines_out, f"LAST-MODIFIED:{now_utc}")

        add_line(lines_out, dtstart_line)
        add_line(lines_out, dtend_line)

        add_line(lines_out, f"SUMMARY:{escape_ics_text(summary_id)}")
        add_line(lines_out, f"DESCRIPTION:{escape_ics_text(description_id)}")

        add_line(lines_out, "STATUS:CONFIRMED")
        add_line(lines_out, "CLASS:PUBLIC")
        add_line(lines_out, "SEQUENCE:0")
        add_line(lines_out, "TRANSP:TRANSPARENT")

        # Opsional untuk Outlook
        add_line(lines_out, "X-MICROSOFT-CDO-ALLDAYEVENT:TRUE")
        add_line(lines_out, "X-MICROSOFT-CDO-BUSYSTATUS:FREE")
        add_line(lines_out, "X-MICROSOFT-CDO-REMINDERMINUTESBEFORESTART:1440")

        # Alarm / reminder 1 hari sebelumnya
        lines_out.append("BEGIN:VALARM")
        add_line(lines_out, "TRIGGER:-P1D")
        add_line(lines_out, "ACTION:DISPLAY")
        add_line(lines_out, "DESCRIPTION:Pengingat hari libur besok")
        lines_out.append("END:VALARM")

        lines_out.append("END:VEVENT")

    lines_out.append("END:VCALENDAR")
    return "\n".join(lines_out) + "\n"

def main():
    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    source_text = response.text
    lines = unfold_ics_lines(source_text)
    events = parse_events(lines)

    calendar_text = build_calendar(events)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(calendar_text, encoding="utf-8")

    print(f"ICS berhasil dibuat: {OUTPUT}")

if __name__ == "__main__":
    main()
