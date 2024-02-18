import argparse

from scryfall_json_to_txt import scryfall_json_to_txt


def main(command_line=None):
    parser = argparse.ArgumentParser(
        prog="mtgutil",
        description="A series of utilities for working with MTG"
    )

    parsers = parser.add_subparsers(title="Utilities", dest="command")
    tcg_parser = parsers.add_parser(name="tcg", help="""
    Scryfall Deck Export JSON/CSV to TCGPlayer Mass Entry Converter
    
    Usage: 
        Provide the path to a JSON file (for filename auto-completion, the name typically starts with "deck-"
        from Scryfall's deck export feature to have it converted
            to a mass entry format consumable by TCGPlayer.
        
        Optionally, provide a path to a destination file (does not have to be made already)
            for the output to be saved as a new file
            
    KNOWN LIMITATIONS:
        This isn't perfect, still. You'll at least know which cards didn't work because TCGPlayer will tell you, 
        and put a dot next to them in the input. There are a few reasons a card will not be recognized in a way that I 
        have not yet automated out.
        
        1. No basic lands. TCGPlayer's mass-entry system does not support them.
                For now, they're translated  at the bottom of your print-out in "UI Search-Friendly-ish" format.
                *ish meaning that we need the set name and apparently the full set name is not deemed necessary for the JSON version.
                So, CSV only
        
        2. Cards with an off-standard printing do not have the designation in Scryfall,
            but they do on TCGPlayer. If some of your cards fail, it may be this. For example, 
                1 Blossoming Bogbeast [C21] 386
                needs to become:
                1 Blossoming Bogbeast (Extended Art) [C21] 386
                
        3. Sometimes, the set code is just different. And I have not taken the time to map the differences yet. :) 
                    
    Good luck!
    """)
    tcg_parser.add_argument("sourcefile", type=str, help="The file to load. Supported file types: CSV, JSON")
    tcg_parser.add_argument("-o", "--out", type=str, help="Where to store the output."
                                                                    " If not provided, it will be printed to stdout.")
    tcg_parser.add_argument("--include", type=str, nargs="*",
                            choices=["all", "commanders", "nonlands", "outside", "lands", "maybeboard"],
                            default=["commanders", "nonlands", "lands"])
    args = parser.parse_args(command_line)

    match args.command:
        case "tcg":
            scryfall_json_to_txt(**vars(args))
        case "default":
            raise ValueError("Invalid value: %s" % args.command or "null")


if __name__ == '__main__':
    main()
