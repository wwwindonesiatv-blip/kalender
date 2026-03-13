import requests
from datetime import datetime, timedelta
from pathlib import Path

COUNTRY_CODE = "ID"
YEARS = [datetime.utcnow().year, datetime.utcnow().year + 1]
OUTPUT = Path("docs/indonesia-holidays.ics")

TRANSLATIONS = {
    "New Year's Day": "Tahun Baru Masehi",
    "Chinese New Year": "Tahun Baru Imlek",
    "Chinese New Year Holiday": "Tahun Baru Imlek",
    "Isra and Mi'raj": "Isra Mikraj Nabi Muhammad SAW",
    "Isra and Miraj": "Isra Mikraj Nabi Muhammad SAW",
    "Balinese New Year": "Hari Suci Nyepi Tahun Baru Saka",
    "Day of Silence": "Hari Suci Nyepi Tahun Baru Saka",
    "Good Friday": "Wafat Isa Al Masih",
    "Eid al-Fitr": "Hari Raya Idulfitri",
    "Eid ul-Fitr": "Hari Raya Idulfitri",
    "Islamic New Year": "Tahun Baru Islam 1 Muharam",
    "Muharram": "Tahun Baru Islam 1 Muharam",
    "Labour Day": "Hari Buruh Internasional",
    "Waisak Day": "Hari Raya Waisak",
    "Vesak Day": "Hari Raya Waisak",
    "Ascension Day of Jesus Christ": "Kenaikan Isa Al Masih",
    "Pancasila Day": "Hari Lahir Pancasila",
    "Eid al-Adha": "Hari Raya Iduladha",
    "Eid ul-Adha": "Hari Raya Iduladha",
    "Islamic New Year Holiday": "Tahun Baru Islam 1 Muharam",
    "Independence Day": "Hari Kemerdekaan Republik Indonesia",
    "The Prophet Muhammad's Birthday": "Maulid Nabi Muhammad SAW",
    "Prophet Muhammad's Birthday": "Maulid Nabi Muhammad SAW",
    "Christmas Day": "Hari Raya Natal",
    "Ascension of the Prophet Muhammad": "Isra Mikraj Nabi Muhammad SAW",
}

def escape_ics_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace(";", r"\;")
            .replace(",", r"\,")
            .replace("\n", r"\n")
    )

def to_indonesian_name(local_name: str, name: str) -> str:
    candidates = [name or "", local_name or ""]
    for item in candidates:
        if item in TRANSLATIONS:
            return TRANSLATIONS[item]

    # fallback jika tidak ditemukan
    if local_name:
        return local_name
    if name:
        return name
    return "Hari Libur"

def build_event(date_str, summary, description, uid_suffix):
    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    end_date = start_date + timedelta(days=1)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    return [
        "BEGIN:VEVENT",
        f"UID:{start_date.strftime('%Y%m%d')}-{uid_suffix}@kalender-libur-indonesia",
        f"DTSTAMP:{timestamp}",
        f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}",
        f"SUMMARY:{escape_ics_text(summary)}",
        f"DESCRIPTION:{escape_ics_text(description)}",
        "LOCATION:Indonesia",
        "STATUS:CONFIRMED",
        "TRANSP:TRANSPARENT",
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
            summary = to_indonesian_name(local_name, name)
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
