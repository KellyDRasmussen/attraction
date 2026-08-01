# ── Region → Kommune mapping ───────────────────────────────────────────────────

REGIONS = {
    "Region Hovedstaden": [
        "Albertslund", "Allerød", "Ballerup", "Bornholm", "Brøndby",
        "Christiansø", "Copenhagen", "Dragør", "Egedal", "Fredensborg",
        "Frederiksberg", "Frederikssund", "Furesø", "Gentofte", "Gladsaxe",
        "Glostrup", "Gribskov", "Halsnæs", "Helsingør", "Herlev",
        "Hillerød", "Høje-Taastrup", "Hørsholm", "Hvidovre", "Ishøj",
        "Lyngby-Taarbæk", "Rudersdal", "Rødovre", "Tårnby", "Vallensbæk",
    ],
    "Region Sjælland": [
        "Faxe", "Greve", "Guldborgsund", "Holbæk", "Kalundborg", "Køge",
        "Lejre", "Lolland", "Næstved", "Odsherred", "Ringsted", "Roskilde",
        "Slagelse", "Solrød", "Sorø", "Stevns", "Vordingborg",
    ],
    "Region Syddanmark": [
        "Aabenraa", "Assens", "Billund", "Esbjerg", "Faaborg-Midtfyn",
        "Fanø", "Fredericia", "Haderslev", "Kerteminde", "Kolding",
        "Langeland", "Middelfart", "Nordfyns", "Nyborg", "Odense",
        "Svendborg", "Sønderborg", "Tønder", "Varde", "Vejen", "Vejle", "Ærø",
    ],
    "Region Midtjylland": [
        "Aarhus", "Favrskov", "Hedensted", "Herning", "Holstebro",
        "Horsens", "Ikast-Brande", "Lemvig", "Norddjurs", "Odder",
        "Randers", "Ringkøbing-Skjern", "Samsø", "Silkeborg",
        "Skanderborg", "Skive", "Struer", "Syddjurs", "Viborg",
    ],
    "Region Nordjylland": [
        "Aalborg", "Brønderslev", "Frederikshavn", "Hjørring",
        "Jammerbugt", "Læsø", "Mariagerfjord", "Morsø", "Rebild",
        "Thisted", "Vesthimmerlands",
    ],
}

# ── Citizenship group definitions ─────────────────────────────────────────────

G7 = {"Canada", "France", "Germany", "Italy", "Japan", "United Kingdom", "USA"}

G20 = G7 | {
    "Argentina", "Australia", "Brazil", "China", "India", "Indonesia",
    "Mexico", "Russia", "Saudi Arabia", "South Africa", "South Korea", "Turkey",
}

CONTINENT = {
    "Europe": {
        "Albania", "Andorra", "Austria", "Belarus", "Belgium",
        "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus",
        "Czech Republic", "Czechoslovakia", "Denmark", "Estonia",
        "Europe not stated", "Finland", "France", "Georgia", "Germany",
        "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kosovo",
        "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta",
        "Moldova", "Monaco", "Montenegro", "Netherlands", "Norway",
        "Poland", "Portugal", "Republic of North Macedonia", "Romania",
        "Russia", "Serbia", "Serbia and Montenegro", "Slovakia",
        "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey",
        "Ukraine", "United Kingdom", "Yugoslavia", "Yugoslavia, Federal Republic",
    },
    "Asia": {
        "Afghanistan", "Armenia", "Asia not stated", "Azerbaijan", "Bahrain",
        "Bangladesh", "Bhutan", "Brunei", "Cambodia", "China", "East Timor",
        "India", "Indonesia", "Iran", "Iraq", "Israel", "Japan", "Jordan",
        "Kazakhstan", "Kuwait", "Kyrgyzstan", "Laos", "Lebanon",
        "Malaysia", "Maldives", "Middle East not stated", "Mongolia",
        "Myanmar", "Nepal", "North Korea", "Oman", "Pakistan",
        "Philippines", "Qatar", "Saudi Arabia", "Singapore", "South Korea",
        "Sri Lanka", "Syria", "Taiwan", "Tajikistan", "Thailand",
        "Turkmenistan", "United Arab Emirates", "Uzbekistan", "Vietnam", "Yemen",
    },
    "Africa": {
        "Africa not stated", "Algeria", "Angola", "Benin", "Botswana",
        "Burkina Faso", "Burundi", "Cameroon", "Cape Verde",
        "Central African Republic", "Chad", "Comoros",
        "Congo, Democratic Republic", "Congo, Republic", "Djibouti",
        "Egypt", "Equatorial Guinea ", "Eritrea", "Eswantini", "Ethiopia",
        "Gabon", "Gambia, The", "Ghana", "Guinea", "Guinea-Bissau",
        "Ivory Coast", "Kenya", "Lesotho", "Liberia", "Libya",
        "Madagascar", "Malawi", "Mali", "Mauritania", "Mauritius",
        "Morocco", "Mozambique", "Namibia", "Niger", "Nigeria",
        "Rwanda", "Sao Tome and Principe", "Senegal", "Seychelles",
        "Sierra Leone", "Somalia", "South Africa", "South Sudan", "Sudan",
        "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
    },
    "North America": {
        "Bahamas", "Barbados", "Belize", "Canada", "Costa Rica", "Cuba",
        "Dominica", "Dominican Republic", "El Salvador", "Grenada",
        "Guatemala", "Haiti", "Honduras", "Jamaica", "Mexico",
        "Nicaragua", "Panama", "Saint Kitts and Nevis", "Saint Lucia",
        "Trinidad and Tobago", "USA",
    },
    "South America": {
        "Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador",
        "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela",
    },
    "Oceania": {
        "Australia", "Fiji", "Nauru", "New Zealand", "Papua New Guinea",
        "Samoa", "Tonga", "Vanuatu",
    },
    "Other / Unknown": {
        "Not stated", "Stateless", "Soviet Union",
    },
}

# Global North: high-income democracies (OECD core + a few others)
GLOBAL_NORTH = {
    "Australia", "Austria", "Belgium", "Canada", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Germany",
    "Greece", "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan",
    "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta", "Monaco",
    "Netherlands", "New Zealand", "Norway", "Poland", "Portugal", "Romania",
    "Slovakia", "Slovenia", "South Korea", "Spain", "Sweden", "Switzerland",
    "United Kingdom", "USA",
}

GLOBAL_NORTH_SOUTH = {
    "Global North": GLOBAL_NORTH,
    "Global South": set(),   # filled below
}

# EU member states (27 members post-Brexit)
EU = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
    "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
    "Spain", "Sweden",
}

# Nordic countries with a favourable immigration arrangement with Denmark
# (Nordic Passport Union / Common Nordic Labour Market — free movement, no visa),
# excluding Denmark itself since Danish citizens aren't immigrants to Denmark
NORDIC = {"Sweden", "Norway", "Finland", "Iceland"}

# Recent political instability — countries with major conflict/displacement since ~2015
INSTABILITY = {
    "Afghanistan", "Belarus", "Burkina Faso", "Central African Republic",
    "Chad", "Congo, Democratic Republic", "Ethiopia", "Guinea",
    "Guinea-Bissau", "Haiti", "Iraq", "Libya", "Mali", "Myanmar",
    "Nicaragua", "Niger", "Russia", "Somalia", "South Sudan", "Sudan",
    "Syria", "Ukraine", "Venezuela", "Yemen", "Zimbabwe",
}


def build_groups(all_citizenships: list[str]) -> dict:
    """
    Given the full list of citizenships in the data, return a dict of
    group_name → {label → frozenset of citizenship strings}.
    Also fills in Global South as everything not Global North (minus unknowns).
    """
    all_set = set(all_citizenships)
    unknown = {"Not stated", "Stateless", "Soviet Union",
               "Czechoslovakia", "Yugoslavia", "Yugoslavia, Federal Republic",
               "Serbia and Montenegro"}

    # Global South = all real countries not in Global North
    global_south = all_set - GLOBAL_NORTH - unknown
    GLOBAL_NORTH_SOUTH["Global South"] = global_south

    return {
        "EU / Non-EU": {
            "EU": EU & all_set,
            "Non-EU": all_set - EU - unknown,
        },
        "Danish / Non-Danish": {
            "Danish": {"Denmark"},
            "Non-Danish": all_set - {"Denmark"} - unknown,
        },
        "Nordic / Non-Nordic": {
            "Nordic": NORDIC & all_set,
            "Non-Nordic": all_set - NORDIC - {"Denmark"} - unknown,
        },
        "G7": {
            "All G7": G7 & all_set,
            **{c: {c} for c in sorted(G7 & all_set)},
        },
        "G20": {
            "All G20": G20 & all_set,
            **{c: {c} for c in sorted(G20 & all_set)},
        },
        "Continent": {
            label: members & all_set
            for label, members in CONTINENT.items()
        },
        "Global North / South": {
            "Global North": GLOBAL_NORTH & all_set,
            "Global South": global_south & all_set,
        },
        "Political instability": {
            "All instability countries": INSTABILITY & all_set,
            **{c: {c} for c in sorted(INSTABILITY & all_set)},
        },
    }
