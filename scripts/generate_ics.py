import requests
from datetime import datetime
from pathlib import Path

COUNTRY_CODE = "ID"
YEARS = [datetime.utcnow().year, datetime.utcnow().year + 1]
OUTPUT = Path("docs/indonesia-holidays.ics")

TRANSLATIONS = {
    "New Year's Day": "Tahun Baru Masehi",
    "Independence Day": "Hari Kemerdekaan Republik Indonesia",
    "Christmas Day": "Hari Raya Natal",
    "Good Friday": "Wafat Isa Al Masih",
    "Labour Day": "Hari Buruh Internasional",
    "Ascension Day of Jesus Christ": "Kenaikan Isa Al Masih",
}

def escape_ics_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace(";", r"\;")
            .replace(",", r"\,")
            .replace("\n", r"\n")
    )

def build_event(date_str, summary, description, uid_suffix):
    start_date = datetime.strptime(date_str, "%Y-%m-%d")
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    start_local = start_date.strftime("%Y%m%d") + "T090000"
    end_local = start_date.strftime("%Y%m%d") + "T100000"

    return [
        "BEGIN:VEVENT",
        f"UID:{start_date.strftime('%Y%m%d')}-{uid_suffix}@kalender-libur-indonesia",
        f"DTSTAMP:{timestamp}",
        f"DTSTART;TZID=Asia/Jakarta:{start_local}",
        f"DTEND;TZID=Asia/Jakarta:{end_local}",
        f"SUMMARY:{escape_ics_text(summary)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
        "LOCATION:Indonesia",
        "STATUS:CONFIRMED",
        "TRANSP:OPAQUE",
        "BEGIN:VALARM",
        "TRIGGER:-P1D",
        "ACTION:DISPLAY",
        "DESCRIPTION:Pengingat hari libur besok",
        "END:VALARM",
        "END:VEVENT",
    ]

def fetch_holidays(year):
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{COUNTRY_CODE}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def main():
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GitHub Actions//Hari Libur Nasional Indonesia//ID",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Hari Libur Nasional Indonesia",
        "X-WR-TIMEZONE:Asia/Jakarta",
        "X-WR-CALDESC:Kalender otomatis hari libur nasional Indonesia",
        "BEGIN:VTIMEZONE",
        "TZID:Asia/Jakarta",
        "X-LIC-LOCATION:Asia/Jakarta",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0700",
        "TZOFFSETTO:+0700",
        "TZNAME:WIB",
        "DTSTART:19700101T000000",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]

    for year in YEARS:
        holidays = fetch_holidays(year)

        for h in holidays:
            if not h.get("global", True):
                continue
            if "Public" not in h.get("types", []):
                continue

            name = h.get("name") or ""
            local_name = h.get("localName") or ""
            summary = TRANSLATIONS.get(name, local_name or name or "Hari Libur")
            description = f"Hari Libur Nasional Indonesia ({year})"

            lines.extend(
                build_event(
                    date_str=h["date"],
                    summary=summary,
                    description=description,
                    uid_suffix=str(year),
                )
            )

    lines.append("END:VCALENDAR")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"ICS berhasil dibuat: {OUTPUT}")

if __name__ == "__main__":
    main()
