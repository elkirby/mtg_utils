import re
from typing import List, Dict, Any
import json

# TODO: We need to start fixing the non-matching set codes
# But I don't want to right now.
SET_CODE_LOOKUP = {
    "sld": {
        "name": "Secret Lair Drop Series",
        "code": "SLD"
    }
}


def fix_name_formatting_quirks(name: str) -> str:
    """
    There are a number of quirks that Scryfall employs during export that does not match TCGPlayer's mass entry format,
        as it relates to the card name.

    This intends to fix those quirks to what TCGPlayer will actually (hopefully) recognize.

    Current replacements:
        "Food Token" -> "Food"
        "Virtue of Strength // Garenbrig Growth" -> "Virtue of Strength"

    :param name: the current name
    :return: the name with any "quirks" removed
    """
    # Remove the following from the name:
    # alternate face name from the card,
    # " Token" suffix e.g. Food Token -> Food
    # the wrapper quotes put around names that have commas in them
    # None are recognized by TCGPlayer

    # Written out regexes for readability/accessibility for those less familiar with regular expressions
    two_faced_card_re = r"\s//\s.*"  # two slashes with a space on either side " // ", plus anything after it
    token_card_re = " Token"  # the word " Token" at the end
    any_of_these = f"({two_faced_card_re}|{token_card_re})"  # As the name suggests. Match any of these
    name: str = re.sub(any_of_these, "", name)

    return name


def fix_set_code(set_code: str) -> str:
    """
    Makes the set code uppercase and fixes instances where it's weird and wrong
    :param set_code:
    :return:
    """
    # TODO: Fix all the times the code is just like, wrong
    return set_code.upper()


def fix_collector_number(collector_number: str) -> str:
    """
    jeez everything's just weird and wrong huh

    :param collector_number:
    :return: do you think scryfall takes open contributions
    """
    remove_these = "★"
    for c in remove_these:
        collector_number = collector_number.replace(c, "")
    return collector_number


def scryfall_json_to_txt(sourcefile: str, include: List[str], out: str = '', **kwargs):
    """
    Transform a decklist csv downloaded from Scryfall to a proper TCGPlayer mass entry txt file

    :param include: The sections to include; lands, nonlands, commanders, maybeboard, outside
    :param sourcefile: the fully-qualified path to the json file
    :param out: what you want the filename to be.
                          if left blank, the output will be printed to stdout.
    :param kwargs: me being lazy and wanting to be able to pass everything to all the command entrypoints
    :return:
    """
    with open(sourcefile, "r") as f:
        deck_list: Dict[Any] = json.loads(f.read())
    formatted_cards: List[str] = []
    lands: List[str] = []

    for card_section, cards in deck_list["entries"].items():
        include_cards = card_section in include or "all" in include
        if include_cards:
            for card in cards:
                count = card["count"]
                card_digest = card["card_digest"]
                name = fix_name_formatting_quirks(card_digest["name"])
                set_code = fix_set_code(card_digest["set"])
                collector_number = fix_collector_number(card_digest['collector_number'])
                if card_digest["name"] in ["Plains", "Mountain", "Forest", "Island", "Swamp"]:
                    # Cool. so they have the set name in the csv, but not the JSON. cool. Sure. Why would they
                    lands.append(f"{name} ({collector_number}) - ({set_code})")
                else:
                    entry_line = "%d %s" % (count, name)
                    # Add printing info if specified
                    if card["printing_specified"]:
                        entry_line += " [%s] %s" % (set_code, collector_number)

                    formatted_cards.append(entry_line)

    formatted_card_content = "\n".join(formatted_cards)
    land_printout = ""
    if lands:
        land_printout = """

-----------------------------------------------------------
| NOTE:                                                    |
| Basic lands are not supported by TCGPlayer's mass entry. |
| Copy these somewhere so you can find them manually.      |
| They should already be in "search-ready" format.         |
-----------------------------------------------------------

"""
        land_printout += "\n".join(lands)

    if out:
        with open(out, "w") as f:
            f.write(formatted_card_content)
    else:
        print(formatted_card_content)

    print(land_printout)
