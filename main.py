"""
The task here is to model the information you are given below, in a reasonable
JSON format. The information is concerning a fictional procurement, and the actors
partaking in it, but it is very much similar to the kind of data you will work with at
x.
Some terms will be worded in a more understandable manner, even if there is a
more appropriate term when using industry language. In these cases, the industry
term will be given in parentheses after the first occurrence of the more common
term.

Task
Structure the below information in a reasonable JSON format. If individual points of
information aren’t given as explicit values, make up some reasonable
placeholders/mocked values at your discretion.
Please bring your JSON to the second interview and you will together with Petter
and Samuel discuss this case during your meeting.
Procurement Information
Stockholm Municipality has published a public procurement, where the goal is to
acquire cleaning services for some of their office buildings. They have divided up
the procurement into two parts (lots), one for the office buildings in southern
Stockholm, one for the ones in northern Stockholm.
For each of these parts, a few suppliers of cleaning services have left bids, meaning
that they want to get the contract, and have sent an offer to the procuring
organisation. For the first (south) part, 4 suppliers left bids. For the second (north), 3
suppliers left bids.
2 of these suppliers left bids on both parts of the procurement.
Each of these suppliers have address information and contact details to contact
persons at the company.
Each bid contains information such as their offered prices - in part hourly rates for
cleaning of different types of rooms in an office building, but also list prices for one
time efforts such as washing of carpets and cleaning of windows.
Eventually, the bids of 2 of the 4 suppliers were chosen as winners for the part
pertaining to southern Stockholm, and one was chosen as winner for northern
Stockholm. The one chosen as winner for northern Stockholm was one of the
winners for the other part as well.
"""

from pprint import pprint

from pydantic import BaseModel

from errors import BidError, LotError


class ContactPerson(BaseModel):
    name: str
    email: str
    phone: str


class Supplier(BaseModel):
    """Company who place bids

    We check whether companies have F-skattsedel at time of placing bid
    and ongoing bankruptcy according to Skatteverket

    The organization_code is a standard code needed to check
    for F-skatt and bankruptcy in Sweden
    """

    name: str
    adress: str
    city: str
    postcode: str
    contact_persons: list[ContactPerson]
    organization_code: str
    fskatt: bool = True
    bankruptcy: bool = False


class ListPrice(BaseModel):
    """We default to SEK"""

    name: str
    price: float
    currency: str = "SEK"
    details: str


class Bid(BaseModel):
    """Bids are placed by suppliers for a specific lot."""

    fixed_prices: list[ListPrice]
    hour_prices: list[ListPrice]
    organization: Supplier
    winner: bool = False


class Lot(BaseModel):
    """Lots are part of a procurement."""

    name: str
    details: str
    bids: list[Bid]

    @property
    def at_least_one_winning_bid(self) -> bool:
        for bid in self.bids:
            if bid.winner is True:
                return True
        return False

    def check_winning_bids_have_fskatt(self):
        for bid in self.get_winning_bids:
            if not bid.organization.fskatt:
                raise BidError(f"{bid.organization.name} is not registered for F-skatt")

    def check_winning_bids_have_not_filed_for_bankruptcy(self):
        for bid in self.get_winning_bids:
            if bid.organization.bankruptcy:
                raise BidError(f"{bid.organization.name} has filed for bankruptcy")

    @property
    def get_winning_bids(self):
        winning_bids = list()
        for bid in self.bids:
            if bid.winner is True:
                winning_bids.append(bid)
        return winning_bids

    @property
    def get_winning_bids_as_dictionaries(self):
        winning_bids = list()
        for bid in self.get_winning_bids:
            winning_bids.append(bid.model_dump())
        return winning_bids


class Procurement(BaseModel):
    """This models a generic procurement with lots and details.

    Implementation notes:

    Since we store this information in MongoDB we
    want to keep track of the version so we can easily
    let improve the format over time and migrate older
    formatted data to new formats if we change the syntax in the future.

    We assume there is some kind of internal ID
    to keep procurements organized according to organization and country.

    We assume all text is in a single language.
    This is not ideal if the database
    and system should supports multiple countries.
    """

    lots: list[Lot]
    name: str
    details: str
    format_version: str = "1"
    organization_id: int = 1

    def check(self):
        """Check that all lots have at least one winning bid,
        that the winners have F-skatt registration and that
        they did not file for bankruptcy"""
        for lot in self.lots:
            if not lot.at_least_one_winning_bid:
                raise LotError(f"Lot '{lot.name}' does not have a winning bid")
            lot.check_winning_bids_have_fskatt()
            lot.check_winning_bids_have_not_filed_for_bankruptcy()
        print("All lots passed the checks")

    def print_winning_bids(self):
        for lot in self.lots:
            if lot.get_winning_bids_as_dictionaries:
                print(f"Winning bids for lot: '{lot.name}':")
                pprint(lot.get_winning_bids_as_dictionaries)


#############
# Mock data #
#############
# North
# bidder Alltvätt
julie = ContactPerson(name="Julie Svensson", phone="12345", email="julie@alltvatt.se")
alltvatt = Supplier(
    name="Alltvätt",
    adress="Allvägen 1",
    postcode="12345",
    city="Norrtälje",
    organization_code="123456-1213",
    contact_persons=[julie],
)
alltvatt_carpet = ListPrice(
    name="washing of carpet", price=150, details="price per carpet up to 2x2m"
)
alltvatt_window = ListPrice(
    name="cleaning of window", price=150, details="price per window up to 2x2m"
)
alltvatt_hourly = ListPrice(
    name="standard hourly rate",
    price=150,
    details="cleaning of floors and emtyping trashcans",
)
alltvatt_north_bid = Bid(
    fixed_prices=[alltvatt_carpet, alltvatt_window],
    hour_prices=[alltvatt_hourly],
    organization=alltvatt,
    winner=True,
)
alltvatt_south_bid = Bid(
    fixed_prices=[alltvatt_carpet, alltvatt_window],
    hour_prices=[alltvatt_hourly],
    organization=alltvatt,
    winner=True,
)
# bidder Städ AB
anna = ContactPerson(name="Anna Svensson", phone="12345", email="anna@stad.se")
stad_ab = Supplier(
    name="Städ AB",
    adress="Allvägen 2",
    postcode="12345",
    city="Norrtälje",
    organization_code="123456-1219",
    contact_persons=[anna],
)
stad_ab_carpet = ListPrice(
    name="washing of carpet", price=175, details="price per carpet up to 2x2m"
)
stad_ab_window = ListPrice(
    name="cleaning of window", price=175, details="price per window up to 2x2m"
)
stad_ab_hourly = ListPrice(
    name="standard hourly rate",
    price=175,
    details="cleaning of floors and emtyping trashcans",
)
stad_ab_north_bid = Bid(
    fixed_prices=[stad_ab_carpet, stad_ab_window],
    hour_prices=[stad_ab_hourly],
    organization=stad_ab,
)
stad_ab_south_bid = Bid(
    fixed_prices=[stad_ab_carpet, stad_ab_window],
    hour_prices=[stad_ab_hourly],
    organization=stad_ab,
    winner=True,
)
# bidder Totalt rent AB
peter = ContactPerson(name="Peter Ren", phone="12345", email="peter@totalt.se")
totalt_ab = Supplier(
    name="Totalt rent AB",
    adress="Allvägen 3",
    postcode="12345",
    city="Norrtälje",
    organization_code="123456-1211",
    contact_persons=[peter],
    bankruptcy=True,
)
totalt_ab_carpet = ListPrice(
    name="washing of carpet", price=195, details="price per carpet up to 2x2m"
)
totalt_ab_window = ListPrice(
    name="cleaning of window", price=175, details="price per window up to 2x2m"
)
totalt_ab_hourly = ListPrice(
    name="standard hourly rate",
    price=195,
    details="cleaning of floors and emtyping trashcans",
)
totalt_ab_bid = Bid(
    fixed_prices=[totalt_ab_carpet, totalt_ab_window],
    hour_prices=[totalt_ab_hourly],
    organization=totalt_ab,
)
# bidder Rent av AB
tomas = ContactPerson(name="Tomas Persson", phone="12345", email="tomas@rentav.se")
rentav_ab = Supplier(
    name="Rent av AB",
    adress="Allvägen 4",
    postcode="12345",
    city="Norrtälje",
    organization_code="123456-1311",
    contact_persons=[tomas],
)
rentav_ab_carpet = ListPrice(
    name="washing of carpet", price=195, details="price per carpet up to 2x2m"
)
rentav_ab_window = ListPrice(
    name="cleaning of window", price=175, details="price per window up to 2x2m"
)
rentav_ab_hourly = ListPrice(
    name="standard hourly rate",
    price=195,
    details="cleaning of floors and emtyping trashcans",
)
rentav_ab_bid = Bid(
    fixed_prices=[rentav_ab_carpet, rentav_ab_window],
    hour_prices=[rentav_ab_hourly],
    organization=rentav_ab,
)
# bidder Cleaning House AB
susann = ContactPerson(
    name="Susann Petterson", phone="12345", email="susann@cleaning.se"
)
cleaning_house = Supplier(
    name="Cleaning House AB",
    adress="Allvägen 4",
    postcode="12345",
    city="Norrtälje",
    organization_code="123456-1211",
    contact_persons=[susann],
    fskatt=False,
)
cleaning_house_carpet = ListPrice(
    name="washing of carpet", price=215, details="price per carpet up to 2x2m"
)
cleaning_house_window = ListPrice(
    name="cleaning of window", price=135, details="price per window up to 2x2m"
)
cleaning_house_hourly = ListPrice(
    name="standard hourly rate",
    price=185,
    details="cleaning of floors and emtyping trashcans",
)
cleaning_house_bid = Bid(
    fixed_prices=[cleaning_house_carpet, cleaning_house_window],
    hour_prices=[cleaning_house_hourly],
    organization=cleaning_house,
)
# 4 suppliers in total
# totalt_ab, rentav_ab only bid on the north lot
# cleaning_house only bid on the south lot
# alltvatt won the bid on both of the lots
# stad_ab won bid on the south lot
north = Lot(
    name="north",
    details="offices in the north part of the city",
    bids=[alltvatt_north_bid, stad_ab_north_bid, totalt_ab_bid, rentav_ab_bid],
)
# 3 suppliers in total
south = Lot(
    name="south",
    details="offices in the north part of the city",
    bids=[alltvatt_south_bid, stad_ab_south_bid, cleaning_house_bid],
)
# Overlap was: 2 suppliers for the lots.
# In this mock alltvatt_bid, stad_ab_bid were the companies that placed bids on both lots.
procurement = Procurement(
    name="Stockholm municipality cleaning procurement 2024",
    details="split in two lots, north and south",
    lots=[north, south],
)

# Check and print
print(procurement.check())
print("All procurement information")
pprint(procurement.model_dump())
procurement.print_winning_bids()

# Write the JSON data to a file
with open("procurement_data.json", "w") as file:
    file.write(procurement.model_dump_json(indent=2))
print("Wrote to file")
