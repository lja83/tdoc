import math
import libtcodpy as tcod

class Piece():
    def __init__(self, x, y, char, lit_color=tcod.white, unlit_color=tcod.darker_grey):
        self.x = x
        self.y = y
        self.char = char
        self.lit_color = lit_color
        self.unlit_color = unlit_color
    
    def draw(self, con, lit):
        if lit:
            color = self.lit_color
        else:
            color = self.unlit_color
        tcod.console_put_char_ex(con, self.x, self.y, self.char, color, tcod.black)

class Tile():
    def __init__(self, char, canPass=False, isTrans=None, lit_color=tcod.white, unlit_color=tcod.darker_grey):
        self.lit_color = lit_color
        self.unlit_color = unlit_color
        self.char = char
        self.canPass = canPass
        if isTrans != None:
            self.isTrans = isTrans
        else:
            self.isTrans = self.canPass
    
    def draw(self, con, x, y, lit):
        if lit:
            color = self.lit_color
        else:
            color = self.unlit_color
        tcod.console_put_char_ex(con, x, y, self.char, color, tcod.black)

class Rect():
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.x2 = x + w
        self.y1 = y
        self.y2 = y + h
    
    def center(self):
        x = ((self.x2 - self.x1) / 2) + self.x1
        y = ((self.y2 - self.y1) / 2) + self.y1
        return (x, y)
    
    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Level():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.create_level()
    
    def create_room(self, rect):
        for x in range(rect.x1+1, rect.x2):
            for y in range(rect.y1+1, rect.y2):
                self.tiles[x][y] = Tile('.', True, True)
    
    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2)):
            self.tiles[x][y] = Tile('.', True, True)
    
    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2)):
            self.tiles[x][y] = Tile('.', True, True)
    
    def create_level(self):
        self.tiles = [[Tile('#')
                        for y in range(self.y)]
                            for x in range(self.x)]
        
        room_min = 8
        room_max = 10
        
        rooms = []
        for i in range(100):
            w = tcod.random_get_int(0, room_min, room_max)
            h = tcod.random_get_int(0, room_min, room_max)
            x = tcod.random_get_int(0, 0, self.x - room_max - 1)
            y = tcod.random_get_int(0, 0, self.y - room_max - 1)
            new_room = Rect(x, y, w, h)
            
            if len(rooms) == 0:
                self.start_x = (new_room.x2 + new_room.x1) / 2
                self.start_y = (new_room.y2 + new_room.y1) / 2
                self.create_room(new_room)
                rooms.append(new_room)
            else:
                failed = False
                for other_room in rooms:
                    if new_room.intersect(other_room):
                        failed = True
                        break
                if not failed:
                    self.create_room(new_room)
                    last_room = rooms[-1]
                    x1, y1 = new_room.center()
                    x2, y2 = last_room.center()
                    self.create_h_tunnel(x1, x2, y1)
                    self.create_v_tunnel(y1, y2, x2)
                    
                    rooms.append(new_room)
    
    def draw(self, con):
        for x in range(self.x):
            for y in range(self.y):
                self.tiles[x][y].draw(con, x, y, True)

class Window():
    def __init__(self, w, h, buffw, buffh):
        self.w = w
        self.h = h
        self.buffh = buffh
        self.buffw = buffw
        self.loc_x = 0
        self.loc_y = 0
        self.layers = {}
        self.orderedLayers = []
        
        self.collapsed_layer = tcod.console_new(buffw, buffh)
    
    def sanify(self):
        if self.loc_x + self.w > self.buffw:
            self.loc_x = self.buffw - self.w
        if self.loc_x < 0:
            self.loc_x = 0
        
        if self.loc_y + self.h > self.buffh:
            self.loc_y = self.buffh - self.h
        if self.loc_y < 0:
            self.loc_y = 0
    
    def scroll(self, dx, dy):
        self.loc_x += dx
        self.loc_y += dy
        self.sanify()
    
    def center_on(self, x, y):
        self.loc_x = x - (self.w / 2)
        self.loc_y = y - (self.h / 2)
        self.sanify()
    
    def new_layer(self, name):
        con = tcod.console_new(self.buffw, self.buffh)
        self.layers[name] = con
        self.orderedLayers.append(con)
        return con
    
    def collapse_layers(self):
        tcod.console_clear(self.collapsed_layer)
        for layer in self.orderedLayers:
            tcod.console_blit(layer, self.loc_x, self.loc_y, self.w, self.h, self.collapsed_layer, self.loc_x, self.loc_y, 1.0, 0.0)
    
    def clear(self):
        for con in self.orderedLayers:
            tcod.console_clear(con)
    
    def draw(self, con, x, y):
        self.collapse_layers()
        tcod.console_blit(self.collapsed_layer, self.loc_x, self.loc_y, self.w, self.h, con, x, y, 1.0, 0.0)

if __name__ == '__main__':
    screen_x = 80
    screen_y = 50
    
    # main console
    tcod.console_init_root(screen_x, screen_y, 'Title', False)
    
    level = Level(80, 40)
    levelWin = Window(40, 25, level.x, level.y)
    mapCon = levelWin.new_layer('map')
    piecesCon = levelWin.new_layer('pieces')
    
    player = Piece(level.start_x, level.start_y, '@')
    levelWin.center_on(player.x, player.y)
    pieces = [player]
    
    while not tcod.console_is_window_closed():
        
        # Render the screen
        for piece in pieces:
            piece.draw(piecesCon, True)
        level.draw(mapCon)
        
        levelWin.draw(0, 0, 0)
        tcod.console_flush()
        
        key = tcod.console_wait_for_keypress(False)
        if key.vk == tcod.KEY_KP6:
            player.x += 1
            # levelWin.scroll(1, 0)
        elif key.vk == tcod.KEY_KP4:
            player.x -= 1
            # levelWin.scroll(-1, 0)
        elif key.vk == tcod.KEY_KP2:
            player.y += 1
            # levelWin.scroll(0, 1)
        elif key.vk == tcod.KEY_KP8:
            player.y -= 1
            # levelWin.scroll(0, -1)
        levelWin.center_on(player.x, player.y)
        
        levelWin.clear()
        tcod.console_clear(0)