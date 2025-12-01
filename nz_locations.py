"""
New Zealand location mapping - suburbs/areas to regions
Used to normalize job locations for filtering
"""

# Main regions (these are the filter options)
REGIONS = [
    "Auckland",
    "Wellington",
    "Christchurch",
    "Hamilton",
    "Tauranga",
    "Dunedin",
    "Queenstown",
    "Palmerston North",
    "Napier-Hastings",
    "Nelson",
    "Rotorua",
    "New Plymouth",
    "Whangarei",
    "Invercargill",
    "Whanganui",
    "Gisborne",
    "Blenheim",
    "Timaru",
    "Other NZ",
    "Remote / Work from Home",
]

# Mapping of location keywords to regions
# Order matters - more specific matches first
LOCATION_MAPPING = {
    # Auckland suburbs and areas
    "Auckland": "Auckland",
    "CBD": "Auckland",  # Usually Auckland CBD
    "North Shore": "Auckland",
    "Takapuna": "Auckland",
    "Albany": "Auckland",
    "Orewa": "Auckland",
    "Hibiscus Coast": "Auckland",
    "Silverdale": "Auckland",
    "Devonport": "Auckland",
    "Birkenhead": "Auckland",
    "Glenfield": "Auckland",
    "Browns Bay": "Auckland",
    "Milford": "Auckland",
    "East Auckland": "Auckland",
    "Howick": "Auckland",
    "Pakuranga": "Auckland",
    "Botany": "Auckland",
    "Manukau": "Auckland",
    "Papatoetoe": "Auckland",
    "Otahuhu": "Auckland",
    "Mangere": "Auckland",
    "Otara": "Auckland",
    "Flat Bush": "Auckland",
    "South Auckland": "Auckland",
    "Papakura": "Auckland",
    "Takanini": "Auckland",
    "Drury": "Auckland",
    "Pukekohe": "Auckland",
    "Waiuku": "Auckland",
    "Franklin": "Auckland",
    "West Auckland": "Auckland",
    "Henderson": "Auckland",
    "Te Atatu": "Auckland",
    "Glen Eden": "Auckland",
    "New Lynn": "Auckland",
    "Avondale": "Auckland",
    "Mt Albert": "Auckland",
    "Pt Chevalier": "Auckland",
    "Grey Lynn": "Auckland",
    "Ponsonby": "Auckland",
    "Parnell": "Auckland",
    "Newmarket": "Auckland",
    "Remuera": "Auckland",
    "Epsom": "Auckland",
    "Mt Eden": "Auckland",
    "Grafton": "Auckland",
    "Penrose": "Auckland",
    "Onehunga": "Auckland",
    "Ellerslie": "Auckland",
    "Greenlane": "Auckland",
    "Mt Wellington": "Auckland",
    "Panmure": "Auckland",
    "Glen Innes": "Auckland",
    "St Heliers": "Auckland",
    "Mission Bay": "Auckland",
    "Kohimarama": "Auckland",
    "Meadowbank": "Auckland",
    "Orakei": "Auckland",
    "Waitakere": "Auckland",
    "Kumeu": "Auckland",
    "Helensville": "Auckland",
    "Whangaparaoa": "Auckland",
    "Rodney": "Auckland",
    "Warkworth": "Auckland",

    # Wellington suburbs and areas
    "Wellington": "Wellington",
    "Lower Hutt": "Wellington",
    "Upper Hutt": "Wellington",
    "Hutt Valley": "Wellington",
    "Porirua": "Wellington",
    "Kapiti": "Wellington",
    "Paraparaumu": "Wellington",
    "Waikanae": "Wellington",
    "Petone": "Wellington",
    "Eastbourne": "Wellington",
    "Wainuiomata": "Wellington",
    "Miramar": "Wellington",
    "Kilbirnie": "Wellington",
    "Lyall Bay": "Wellington",
    "Island Bay": "Wellington",
    "Newtown": "Wellington",
    "Mt Victoria": "Wellington",
    "Te Aro": "Wellington",
    "Thorndon": "Wellington",
    "Kelburn": "Wellington",
    "Karori": "Wellington",
    "Johnsonville": "Wellington",
    "Tawa": "Wellington",
    "Churton Park": "Wellington",
    "Khandallah": "Wellington",
    "Ngaio": "Wellington",
    "Wadestown": "Wellington",
    "Brooklyn": "Wellington",
    "Mornington": "Wellington",
    "Berhampore": "Wellington",
    "Seatoun": "Wellington",
    "Strathmore": "Wellington",
    "Hataitai": "Wellington",
    "Masterton": "Wellington",
    "Carterton": "Wellington",
    "Greytown": "Wellington",
    "Featherston": "Wellington",
    "Wairarapa": "Wellington",

    # Christchurch suburbs and areas
    "Christchurch": "Christchurch",
    "Canterbury": "Christchurch",
    "Addington": "Christchurch",
    "Riccarton": "Christchurch",
    "Ilam": "Christchurch",
    "Fendalton": "Christchurch",
    "Merivale": "Christchurch",
    "Papanui": "Christchurch",
    "Bishopdale": "Christchurch",
    "Burnside": "Christchurch",
    "Avonhead": "Christchurch",
    "Hornby": "Christchurch",
    "Sockburn": "Christchurch",
    "Wigram": "Christchurch",
    "Halswell": "Christchurch",
    "Spreydon": "Christchurch",
    "Sydenham": "Christchurch",
    "Cashmere": "Christchurch",
    "St Martins": "Christchurch",
    "Opawa": "Christchurch",
    "Woolston": "Christchurch",
    "Ferrymead": "Christchurch",
    "Sumner": "Christchurch",
    "Lyttelton": "Christchurch",
    "Linwood": "Christchurch",
    "Phillipstown": "Christchurch",
    "Waltham": "Christchurch",
    "St Albans": "Christchurch",
    "Edgeware": "Christchurch",
    "Mairehau": "Christchurch",
    "Shirley": "Christchurch",
    "Richmond": "Christchurch",
    "Avonside": "Christchurch",
    "Dallington": "Christchurch",
    "Burwood": "Christchurch",
    "Parklands": "Christchurch",
    "New Brighton": "Christchurch",
    "Kaiapoi": "Christchurch",
    "Rangiora": "Christchurch",
    "Rolleston": "Christchurch",
    "Lincoln": "Christchurch",
    "Prebbleton": "Christchurch",
    "Selwyn": "Christchurch",
    "Waimakariri": "Christchurch",
    "Belfast": "Christchurch",
    "Northwood": "Christchurch",
    "Redwood": "Christchurch",
    "Harewood": "Christchurch",
    "Russley": "Christchurch",
    "Yaldhurst": "Christchurch",
    "Templeton": "Christchurch",
    "Ashburton": "Christchurch",

    # Hamilton and Waikato
    "Hamilton": "Hamilton",
    "Waikato": "Hamilton",
    "Cambridge": "Hamilton",
    "Te Awamutu": "Hamilton",
    "Morrinsville": "Hamilton",
    "Matamata": "Hamilton",
    "Ngaruawahia": "Hamilton",
    "Huntly": "Hamilton",
    "Raglan": "Hamilton",
    "Frankton": "Hamilton",
    "Claudelands": "Hamilton",
    "Hamilton East": "Hamilton",
    "Hamilton Central": "Hamilton",
    "Hillcrest": "Hamilton",
    "Rototuna": "Hamilton",
    "Te Rapa": "Hamilton",
    "Dinsdale": "Hamilton",

    # Tauranga and Bay of Plenty
    "Tauranga": "Tauranga",
    "Bay of Plenty": "Tauranga",
    "Mt Maunganui": "Tauranga",
    "Mount Maunganui": "Tauranga",
    "Papamoa": "Tauranga",
    "Te Puke": "Tauranga",
    "Whakatane": "Tauranga",
    "Katikati": "Tauranga",
    "Omokoroa": "Tauranga",
    "Bethlehem": "Tauranga",
    "Greerton": "Tauranga",
    "Pyes Pa": "Tauranga",
    "Welcome Bay": "Tauranga",

    # Dunedin and Otago
    "Dunedin": "Dunedin",
    "Otago": "Dunedin",
    "Mosgiel": "Dunedin",
    "Port Chalmers": "Dunedin",
    "St Kilda": "Dunedin",
    "South Dunedin": "Dunedin",
    "North Dunedin": "Dunedin",
    "Oamaru": "Dunedin",
    "Balclutha": "Dunedin",
    "Alexandra": "Dunedin",
    "Cromwell": "Dunedin",
    "Central Otago": "Dunedin",

    # Queenstown
    "Queenstown": "Queenstown",
    "Arrowtown": "Queenstown",
    "Frankton": "Queenstown",
    "Wanaka": "Queenstown",
    "Queenstown-Lakes": "Queenstown",

    # Palmerston North and Manawatu
    "Palmerston North": "Palmerston North",
    "Manawatu": "Palmerston North",
    "Feilding": "Palmerston North",
    "Levin": "Palmerston North",
    "Horowhenua": "Palmerston North",

    # Napier-Hastings / Hawke's Bay
    "Napier": "Napier-Hastings",
    "Hastings": "Napier-Hastings",
    "Hawke's Bay": "Napier-Hastings",
    "Hawkes Bay": "Napier-Hastings",
    "Havelock North": "Napier-Hastings",
    "Taradale": "Napier-Hastings",
    "Flaxmere": "Napier-Hastings",

    # Nelson / Tasman
    "Nelson": "Nelson",
    "Tasman": "Nelson",
    "Richmond": "Nelson",
    "Motueka": "Nelson",
    "Stoke": "Nelson",

    # Rotorua
    "Rotorua": "Rotorua",
    "Lakes": "Rotorua",
    "Taupo": "Rotorua",

    # New Plymouth / Taranaki
    "New Plymouth": "New Plymouth",
    "Taranaki": "New Plymouth",
    "Stratford": "New Plymouth",
    "Hawera": "New Plymouth",
    "Inglewood": "New Plymouth",
    "Waitara": "New Plymouth",

    # Whangarei / Northland
    "Whangarei": "Whangarei",
    "Northland": "Whangarei",
    "Kerikeri": "Whangarei",
    "Paihia": "Whangarei",
    "Kaitaia": "Whangarei",
    "Dargaville": "Whangarei",

    # Invercargill / Southland
    "Invercargill": "Invercargill",
    "Southland": "Invercargill",
    "Gore": "Invercargill",
    "Te Anau": "Invercargill",

    # Whanganui
    "Whanganui": "Whanganui",
    "Wanganui": "Whanganui",

    # Gisborne
    "Gisborne": "Gisborne",
    "East Coast": "Gisborne",

    # Blenheim / Marlborough
    "Blenheim": "Blenheim",
    "Marlborough": "Blenheim",
    "Picton": "Blenheim",

    # Timaru
    "Timaru": "Timaru",
    "South Canterbury": "Timaru",

    # Remote/WFH
    "Remote": "Remote / Work from Home",
    "Work from Home": "Remote / Work from Home",
    "WFH": "Remote / Work from Home",
    "Anywhere": "Remote / Work from Home",
    "New Zealand": "Remote / Work from Home",
    "NZ Wide": "Remote / Work from Home",
}


def get_region(location: str) -> str:
    """
    Determine the region from a location string.
    Returns the region name or 'Other NZ' if not found.
    """
    if not location:
        return "Other NZ"

    location_lower = location.lower().strip()

    # Check each mapping (case-insensitive)
    for keyword, region in LOCATION_MAPPING.items():
        if keyword.lower() in location_lower:
            return region

    # Check if it's a known region name directly
    for region in REGIONS:
        if region.lower() in location_lower:
            return region

    return "Other NZ"


def get_all_regions() -> list:
    """Return list of all regions for filter dropdown"""
    return REGIONS.copy()
