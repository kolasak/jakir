from configuration import load_configuration
if __name__ == "__main__":
    game_map = load_configuration()
    for row in game_map:
        print(row)