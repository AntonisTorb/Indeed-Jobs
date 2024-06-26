import datetime
from pathlib import Path
import re


def maintain_log(log_path: Path, days: int) -> None:
    '''Function to maintain the log file by removing entries older than `days` days.'''

    if not log_path.exists():
        return
    
    new_log: str = ""
    add_rest: bool = False
    first_timestamp: bool = True

    with open(log_path, "r") as f:
        log_lines: list[str] = f.readlines()

    for index, line in enumerate(log_lines):
        parts: list[str] = line.split("|")
        if not len(parts) == 4:
            continue
        date: str = parts[0][:-4]
        timestamp: float = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp()

        cutoff: int = days * 24 * 60 * 60  # Remove logs older than `days` days.
        
        if datetime.datetime.now().timestamp() - timestamp > cutoff:
            first_timestamp = False
            continue
        if first_timestamp:  # First timestamp is not older than 30 days, no need to continue.
            return
        if not add_rest:
            add_rest = True
        
        if add_rest:
            rest: str = "".join(log_lines[index:])
            new_log = f'{new_log}{rest}'
            break

    with open(log_path, "w") as f:
        f.write(new_log)


DISCORD_HELP = '''# Help:
## Config Channel:
`!close            `: Close application.

## Notification Channel:
- React with ✅ to mark interested, or ❌ to delete message.
- Reply with the following commands to swap/set the related field in the database for `job id` in the original message

`!interview {operation} `: Increases/decreases interviews by depending on operation: `+`(default) or `-`.
`!applied:              `: Swaps value for `applied` boolean.
`!response:             `: Swaps value for `response` boolean.
`!rejected:             `: Swaps value for `rejected` boolean.
`!offer:                `: Swaps value for `job_offer` boolean.

For complete documentation please visit: https://github.com/AntonisTorb/Indeed-Jobs'''
 
REGEX_ID_FROM_DISCORD: re.Pattern = re.compile(r"\*\*Id\*\*: ([0-9]+)")

INDEED_COUNTRIES = {
    "argentina": "ar",
    "australia": "au",
    "austria": "at",
    "bahrain": "bh",
    "belgium": "be",
    "brazil": "br",
    "canada": "ca",
    "chile": "cl",
    "china": "cn",
    "colombia": "co",
    "costa rica": "cr",
    "czech republic": "cz",
    "denmark": "dk",
    "ecuador": "ec",
    "egypt": "eg",
    "finland": "fi",
    "france": "fr",
    "germany": "de",
    "greece": "gr",
    "hong kong": "hk",
    "hungary": "hu",
    "india": "in",
    "indonesia": "id",
    "ireland": "ie",
    "israel": "il",
    "italy": "it",
    "japan": "jp",
    "kuwait": "kw",
    "luxembourg": "lu",
    "malaysia": "malaysia",
    "mexico": "mx",
    "morocco": "ma",
    "netherlands": "nl",
    "new zealand": "nz",
    "nigeria": "ng",
    "norway": "no",
    "oman": "om",
    "pakistan": "pk",
    "panama": "pa",
    "peru": "pe",
    "philippines": "ph",
    "poland": "pl",
    "portugal": "pt",
    "qatar": "qa",
    "romania": "ro",
    "saudi arabia": "sa",
    "singapore": "sg",
    "south africa": "za",
    "south korea": "kr",
    "spain": "es",
    "sweden": "se",
    "switzerland": "ch",
    "taiwan": "tw",
    "thailand": "th",
    "turkey": "tr",
    "ukraine": "ua",
    "united arab emirates": "ae",
    "united kingdom": "uk",
    "united states": "www",
    "uruguay": "uy",
    "venezuela": "ve",
    "vietnam": "vn"
}