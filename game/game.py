import libtcodpy as tcod

MAP_WIDTH = 80
MAP_HEIGHT = 45

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

class Asset():
    def __init__(self, x, y, char, name, color, con=0, blocks=False):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.con = con
        self.blocks = blocks
    
    def move(self, dx, dy, dmap):
        if not dmap.blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
    
    def draw(self):
        tcod.console_set_foreground_color(self.con, self.color)
        tcod.console_put_char(self.con, self.x, self.y, self.char, tcod.BKGND_NONE)
    
    def clear(self):
        tcod.console_put_char(self.con, self.x, self.y, ' ', tcod.BKGND_NONE)

class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight
        
        self.explored = False

class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
    
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)
    
    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Map:
    def __init__(self, width, height, con=0):
        self.width = width
        self.height = height
        self.con = con
        self.start_x = 1
        self.start_y = 1
        
        self.max_room_monsters = 3
        
        self.fov_algo = tcod.FOV_RESTRICTIVE
        self.fov_light_walls = True
        self.torch_radius = 10
        
        self.monsters = []
        self.make_map()
    
    def place_objects(self, room):
        num_monsters = tcod.random_get_int(0, 0, self.max_room_monsters)
        
        for i in range(num_monsters):
            x = tcod.random_get_int(0, room.x1+1, room.x2-1)
            y = tcod.random_get_int(0, room.y1+1, room.y2-1)
            
            if tcod.random_get_int(0, 0, 100) < 80:
                monster = Asset(x, y, 'o', 'Orc', tcod.desaturated_green, self.con)
            else:
                monster = Asset(x, y, 'T', 'Troll', tcod.darker_green, self.con)
            
            self.monsters.append(monster)
    
    def make_map(self, width=None, height=None):
        if width == None:
            width = self.width
        if height == None:
            height = self.height
        
        self.tiles = [[ Tile(True)
        for y in range(height)]
            for x in range(width)]
        
        rooms = []
        for r in range(MAX_ROOMS):
            w = tcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = tcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            
            x = tcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
            y = tcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
            
            new_room = Rect(x, y, w, h)
            failed = False
            for other_room in rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break
            if not failed:
                self.create_room(new_room)
                self.place_objects(new_room)
                (new_x, new_y) = new_room.center()
                if len(rooms) == 0:
                    self.start_x = new_x
                    self.start_y = new_y
                else:
                    (prev_x, prev_y) = rooms[-1].center()
                    
                    if tcod.random_get_int(0, 0, 1) == 1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                rooms.append(new_room)
        
        self.fov_map = tcod.map_new(self.width, self.height)
        for y in range(self.height):
            for x in range(self.width):
                tcod.map_set_properties(self.fov_map, x, y, not self.tiles[x][y].blocked, not self.tiles[x][y].block_sight)
    
    def blocked(self, x, y):
        return self.tiles[x][y].blocked
    
    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
    
    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
    
    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
    
    def fov_recompute(self, x, y):
        tcod.map_compute_fov(self.fov_map, x, y,
            self.torch_radius, self.fov_light_walls, self.fov_algo)
    
    def draw(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[x][y].block_sight:
                    char = '#'
                else:
                    char = '.'
                
                if tcod.map_is_in_fov(self.fov_map, x, y):
                    if char == '#':
                        color = tcod.dark_yellow
                    else:
                        color = tcod.grey
                    self.tiles[x][y].explored = True
                else:
                    color = tcod.darker_grey
                
                if self.tiles[x][y].explored:
                    tcod.console_put_char_ex(self.con, x, y, char, color, tcod.black)

class Game:
    def __init__(self, width, height):
        self.screen_width = width
        self.screen_height = height
        self.assets = []
        
        tcod.console_init_root(self.screen_width, self.screen_height, 'Wicked Cool Shit', False)
        self.con = tcod.console_new(self.screen_width, self.screen_height)
    
    def main(self):
        self.map = Map(MAP_WIDTH, MAP_HEIGHT, self.con)
        
        self.player = Asset(self.map.start_x, self.map.start_y, '@', 'player', tcod.white, self.con)
        self.map.fov_recompute(self.player.x, self.player.y)
        
        self.assets.append(self.player)
        self.assets.extend(self.map.monsters)
        
        self.bind_keys()
        
        # tcod.console_credits()
        # tcod.console_clear(0)
        self.player_action = None
        self.game_state = 'playing'
        while not tcod.console_is_window_closed():
            self.render_all()
            
            self.player_action = self.handle_keys()
            if self.player_action == 'exit':
                break
    
    def is_blocked(x, y):
        if self.map.tiles[x][y].blocked:
            return True
        for asset in assets:
            if asset.blocks and asset.x == x and asset.y == y:
                return True
        return False
    
    def handle_keys(self):
        key = tcod.console_wait_for_keypress(True)
        if self.game_state == 'playing':
            if key.vk in self.turn_bindings:
                action = self.turn_bindings[key.vk]
                result = action[0](*action[1])
                if action[2]:
                    self.map.fov_recompute(self.player.x, self.player.y)
                return result
        else:
            return 'didnt-take-turn'
    
    def bind_keys(self):
        move_up         = (self.player.move, [ 0, -1, self.map], True)
        move_down       = (self.player.move, [ 0,  1, self.map], True)
        move_left       = (self.player.move, [-1,  0, self.map], True)
        move_right      = (self.player.move, [ 1,  0, self.map], True)
        move_up_left    = (self.player.move, [-1, -1, self.map], True)
        move_up_right   = (self.player.move, [ 1, -1, self.map], True)
        move_down_left  = (self.player.move, [-1,  1, self.map], True)
        move_down_right = (self.player.move, [ 1,  1, self.map], True)
        quit            = (lambda : 'exit', [], False)
        
        self.turn_bindings = {
            tcod.KEY_UP: move_up,
            tcod.KEY_DOWN: move_down,
            tcod.KEY_LEFT: move_left,
            tcod.KEY_RIGHT: move_right,
            
            tcod.KEY_KP7: move_up_left,
            tcod.KEY_KP8: move_up,
            tcod.KEY_KP9: move_up_right,
            tcod.KEY_KP4: move_left,
            tcod.KEY_KP6: move_right,
            tcod.KEY_KP1: move_down_left,
            tcod.KEY_KP2: move_down,
            tcod.KEY_KP3: move_down_right,
            
            tcod.KEY_ESCAPE: quit,
        }
    
    def render_all(self):
        # color_dark_wall = tcod.Color(0, 0, 100)
        # color_dark_ground = tcod.Color(50, 50, 150)
        
        self.map.draw()
        for asset in self.assets[::-1]:
            if tcod.map_is_in_fov(self.map.fov_map, asset.x, asset.y):
                asset.draw()
        
        tcod.console_blit(self.con, 0, 0, self.screen_width, self.screen_height, 0, 0, 0)
        tcod.console_flush()
        
        tcod.console_clear(self.con)
        # for asset in assets:
        #   asset.clear()

if __name__ == '__main__':
    game = Game(80, 50)
    game.main()