# file which manages procedual generation:
from __future__ import annotations

import math

from game_map import GameMap
import tile_types
import random
from typing import Iterator, Tuple, List, TYPE_CHECKING

import tcod
from entity import Entity

# determines a chunck of the walls to be carved
if TYPE_CHECKING:
    from entity import Entity

# Rectangular room class
class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    # determines center of chunk
    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        if isinstance(other, RectangularRoom):
            return (
                    self.x1 <= other.x2 and
                    self.x2 >= other.x1 and
                    self.y1 <= other.y2 and
                    self.y2 >= other.y1
            )
        elif isinstance(other, CircularRoom):
            # Check if the circular room intersects with the rectangular room
            closest_x = max(self.x1, min(other.center_x, self.x2))
            closest_y = max(self.y1, min(other.center_y, self.y2))
            distance_x = other.center_x - closest_x
            distance_y = other.center_y - closest_y
            return (distance_x ** 2 + distance_y ** 2) <= (other.radius ** 2)


# Ciruclar Room Class
class CircularRoom:
    def __init__(self, center_x: int, center_y: int, radius: int):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius

    @property
    def center(self) -> Tuple[int, int]:
        return self.center_x, self.center_y

    @property
    def inner(self) -> tuple[list[int], list[int]]:
        """Return the inner area of this room as a 2D array index."""
        # Calculate the bounding box of the circle
        x_start = max(0, self.center_x - self.radius)
        x_end = min(self.center_x + self.radius + 1, 100)  # Adjust 100 to your array size
        y_start = max(0, self.center_y - self.radius)
        y_end = min(self.center_y + self.radius + 1, 100)  # Adjust 100 to your array s

        circle = []
        x_values = []
        y_values = []
        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                if math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2) < self.radius:
                    circle.append([x, y])
                    x_values.append(x)
                    y_values.append(y)

        return x_values, y_values

    def intersects(self, other) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        if isinstance(other, RectangularRoom):
            return other.intersects(self)  # Let the RectangularRoom handle intersection with CircularRoom
        elif isinstance(other, CircularRoom):
            # Check if the circular rooms intersect
            distance_x = self.center_x - other.center_x
            distance_y = self.center_y - other.center_y
            distance_squared = distance_x ** 2 + distance_y ** 2
            combined_radius = self.radius + other.radius
            return distance_squared <= combined_radius ** 2


# Create a list of positions that connect 2 rooms
def tunnel_between(
        start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically. - start postion
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2
    # Generate the coordinates for this tunnel. Uses bresenham to generate a straight line tunnel. between th 2 points
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y  # uses yeild key word to suspend the function per call - saves memory


# Identify's/ marks where dungeons are located

def generate_dungeon(
        rect_rooms: int,
        room_min_size: int,
        room_max_size: int,
        map_width: int,
        map_height: int,
        circ_rooms: int,
        max_radius: int,
        min_radius: int,
        player: Entity,

) -> GameMap:
    """Generate a new dungeon map."""
    dungeon = GameMap(map_width, map_height)

    rooms: List = []

    for j in range(rect_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.x, player.y = new_room.center
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor
        # spawn in enemies

        #append the new room to the list.
        rooms.append(new_room)

        for i in range(circ_rooms):

            room_radius = random.randint(min_radius, max_radius)

            # determines position
            x = random.randint(0, dungeon.width - room_width - 1)
            y = random.randint(0, dungeon.height - room_height - 1)

            # "RectangularRoom" class makes rectangles easier to work with
            new_room = CircularRoom(x, y, room_radius)

            # Run through the other rooms and see if they intersect with this one.
            if any(new_room.intersects(other_room) for other_room in rooms):
                continue  # This room intersects, so go to the next attempt.
            # If there are no intersections then the room is valid.

            # Dig out this rooms inner area.
            dungeon.tiles[new_room.inner] = tile_types.floor

            if len(rooms) == 0:
                # The first room, where the player starts.
                player.x, player.y = new_room.center
            else:  # All rooms after the first.
                # Dig out a tunnel between this room and the previous one.
                for x, y in tunnel_between(rooms[-1].center, new_room.center):
                    dungeon.tiles[x, y] = tile_types.floor
            #append the new room to the list.
            rooms.append(new_room)
    return dungeon


"""
PLAN TO INTERGATE FUNCTIONS

add all rooms to the same list
determine class 
run respecitve code to generate random shape.
if other.class = ! circle.
check if center + radius < other.center.
 
"""
