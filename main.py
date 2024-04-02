#!/usr/bin/env python3
import tcod

from engine import Engine
from entity import Entity
from input_handlers import EventHandler
from procgen import generate_dungeon


def main() -> None:
    screen_width = 80
    screen_height = 50
    map_width = 80
    map_height = 45

    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )
    event_handler = EventHandler()

    player = Entity(int(screen_width / 2), int(screen_height / 2), "@", (255, 255, 255))
    exit = Entity(int(screen_width / 2 - 5), int(screen_height / 2), "@", (255, 255, 0))
    entities = {exit, player}

    game_map = generate_dungeon(
        rect_rooms=3,
        room_min_size=2,
        room_max_size=10,
        map_width=map_width,
        map_height=map_height,
        circ_rooms=2,
        max_radius=4,
        min_radius=1,
        player=player
    )
    engine = Engine(entities=entities, event_handler=event_handler, game_map=game_map, player=player)

    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Epic Video Game",
        vsync=True,
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        while True:
            engine.render(console=root_console, context=context)

            events = tcod.event.wait()

            engine.handle_events(events)


if __name__ == "__main__":
    main()

    """
    Parts relating to setting up tcod were taken from here: https://github.com/TStand90/tcod_tutorial_v2/tree/2020/part-3
    Parts of the game I which I developed are within the procedual generation file and main file.
    """

