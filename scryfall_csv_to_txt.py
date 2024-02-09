import re
import sys
from typing import List, Tuple


def normalize_name(idx_name: int, card: List[str], expected_num_columns: int) -> Tuple[str, int]:
    """
    Checks whether a card name was inadvertently split because it had commas in it, and if it did,
     rejoin the name to its full original value, with quotation marks removed.

    CSV exporters will wrap a value that has a comma in it in quotation marks.
    Since we just split the card's row on commas, this means that a card name with one or more commas in it
        will be split into multiple segments, where the beginning and end segments feature a quotation mark.

    Example: (card "name" used for illustrative purposes
        Input: Kurbis, Harvest Celebrant
        CSV Translation: "Kurbis, Harvest Celebrant"
        What it would look like now: ['"Kurbis', ' Harvest Celebrant"']

    :param idx_name: the index of (at least) the beginning of the name in the row
    :param card: all the values that make up the card
    :param expected_num_columns how many values we expected to be in the card.
                                a number higher than we expected would indicate that one of the cells contained a comma.
    :return: the new name value, and the offset to use to obtain the set code/collector number
    """
    name_offset: int = 0
    name: str = card[idx_name]
    if name.startswith('"') and len(card) > expected_num_columns:
        name_pieces: List[str] = [name]
        current_str = card[idx_name]
        # Most likely, the offset will end up being 1. But this is written to handle it being 2 or more
        # By checking whether the current cell being pointed to ends with "
        while not current_str.endswith('"'):
            name_offset += 1
            current_str = card[idx_name + name_offset]
            name_pieces.append(current_str)
        # Re-join name with its commas, and cut off the surrounding quotation marks
        name = ",".join(name_pieces).strip('"')

    return name, name_offset


def fix_other_name_formatting_quirks(name: str):
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
    token_card_re = "\sToken$"  # the word " Token" at the end
    any_of_these = f"({two_faced_card_re}|{token_card_re})"  # As the name suggests. Match any of these
    name: str = re.sub(any_of_these, "", name)

    return name


def main(src_csv: str, dest_filename: str = ''):
    """
    Transform a decklist csv downloaded from Scryfall to a proper TCGPlayer mass entry txt file

    :param src_csv: the fully-qualified path to the csv file
    :param dest_filename: what you want the filename to be.
                          if left blank, the output will be printed to stdout.
    :return:
    """
    with open(src_csv, "r") as csv_file:
        # Read in the lines, split into cells by comma delimiter
        lines = [line.split(",") for line in csv_file.readlines()]
        # Top line is the headers, the rest are the rows
        csv_column_names, cards = lines[0], lines[1:]
        # Get the indices of our target columns (those necessary for TCGPlayer mass entry)
        idx_count = csv_column_names.index("count")
        idx_name = csv_column_names.index("name")

        new_lines: List[str] = []
        lands: List[str] = []
        for card in cards:
            count = card[idx_count]

            # Fix any issues with the name potentially being split by commas
            name, name_offset = normalize_name(idx_name, card, len(csv_column_names))
            name = fix_other_name_formatting_quirks(name)

            # Get the other values
            idx_code = csv_column_names.index("set_code") + name_offset
            idx_num = csv_column_names.index("collector_number") + name_offset
            set_code = card[idx_code]
            num = card[idx_num]

            if name in ["Plains", "Mountain", "Forest", "Island", "Swamp"]:
                lands.append(f"{name} ({num}) - {card[idx_code - 1]} ({set_code.upper()})")
            else:
                new_lines.append(f"{count} {name} [{set_code.upper()}] {num}")
        formatted_card_content = "\n".join(new_lines)
        formatted_card_content += """

-----------------------------------------------------------
| NOTE:                                                    |
| Basic lands are not supported by TCGPlayer's mass entry. |
| Copy these somewhere so you can find them manually.      |
| They should already be in "search-ready" format.         |
-----------------------------------------------------------

"""
        formatted_card_content += "\n".join(lands)
        if dest_filename:
            with open(dest_filename, "w") as f:
                f.write(formatted_card_content)
        else:
            print(formatted_card_content)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:

        print("""
Scryfall Deck Export CSV to TCGPlayer Mass Entry Converter
Usage: 
    Provide the path to a CSV file (for filename auto-completion, the name typically starts with "deck-"
    from Scryfall's deck export feature to have it converted
        to a mass entry format consumable by TCGPlayer.
    
    Optionally, provide a path to a destination file (does not have to be made already)
        for the output to be saved as a new file
        
KNOWN LIMITATIONS:
    This isn't perfect, still. You'll at least know which cards didn't work because TCGPlayer will tell you, 
    and put a dot next to them in the input. There are a few reasons a card will not be recognized in a way that I 
    have not yet automated out.
    
    1. No basic lands. TCGPlayer's mass-entry system does not support them.
            For now, they're translated  at the bottom of your print-out in "UI Search-Friendly" format.
    
    2. Cards with an off-standard printing do not have the designation in Scryfall,
        but they do on TCGPlayer. If some of your cards fail, it may be this. For example, 
            1 Blossoming Bogbeast [C21] 386
            needs to become:
            1 Blossoming Bogbeast (Extended Art) [C21] 386
            
    3. Sometimes, the set code is just different. And I have not taken the time to map the differences yet. :) 
                
Good luck!  
""")
        exit(0)
    else:
        main(*args)
