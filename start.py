import pygame
import sys
import math
import secp256k1 as ice
# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
DARK_GOLD = (184, 134, 11)
ORANGE = (255, 165, 0)
DARK_BLUE = (0, 0, 139)
LIGHT_BLUE = (173, 216, 230)
# Target addresses for each puzzle
TARGETS = {
    'puzzle17': '1HduPEXZRdG26SUT5Yk83mLkPyjnZuJ7Bm',
    'puzzle21': '14oFNXucftsHiUMY8uctg6N487riuyXs4h',
    'puzzle25': '15JhYXn6Mx3oF4Y7PcTAv2wVVAuCFFQNiP',
    'puzzle73': '12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4'
}


def shuffle_string(s):
    char_list = list(s)
    random.shuffle(char_list)
    return ''.join(char_list)
    
def rotate_hex(hex_string):
    # Precompute a translation table for all hex digits
    translation_table = str.maketrans("0123456789abcdef", "123456789abcdef0")
    return hex_string.translate(translation_table)

def shift_left(s, n):
    n = n % len(s)
    return s[n:] + s[:n]
def inverse(binary_string):
    # Ensure the input is valid
    if not all(char in '01' for char in binary_string):
        raise ValueError("Input string must contain only '0' and '1'")
    
    return ''.join('1' if char == '0' else '0' for char in binary_string)


class Button:
    def __init__(self, x, y, width, height, text, font, text_color, bg_color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.current_color = bg_color
        self.is_hovered = False
        
    def draw(self, screen):
        # Draw button with rounded corners
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, self.text_color, self.rect, 3, border_radius=10)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.is_hovered else self.bg_color
        
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click[0]

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_started = False
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 48)
        
        # Create buttons
        button_width = 200
        button_height = 60
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        
        self.start_button = Button(
            button_x, 350, button_width, button_height,
            "Start", self.button_font, WHITE, DARK_BLUE, LIGHT_BLUE
        )
        
        self.exit_button = Button(
            button_x, 450, button_width, button_height,
            "Exit", self.button_font, WHITE, DARK_BLUE, LIGHT_BLUE
        )
        
        # Animation variables
        self.time = 0
        self.particles = []
        self.create_particles()
        
        # Try to load music (won't work without actual mp3 file)
        self.music_loaded = False
        try:
            pygame.mixer.music.load("menu_music.mp3")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # Loop forever
            self.music_loaded = True
        except:
            print("Note: menu_music.mp3 not found. Add your own MP3 file to enable music.")
    
    def create_particles(self):
        # Create bitcoin-themed particles
        import random
        for _ in range(50):  # Increased from 20 to 50
            self.particles.append({
                'x': pygame.math.Vector2(random.randint(0, SCREEN_WIDTH), random.randint(-SCREEN_HEIGHT, 0)),
                'speed': pygame.math.Vector2(random.uniform(-0.5, 0.5), random.uniform(1, 3)),
                'size': random.randint(10, 25),
                'rotation': 0,
                'rotation_speed': random.uniform(-2, 2)
            })
    
    def update_particles(self):
        import random
        for particle in self.particles:
            particle['x'] += particle['speed']
            particle['rotation'] += particle['rotation_speed']
            
            # Wrap around screen
            if particle['x'].x > SCREEN_WIDTH + 50:
                particle['x'].x = random.randint(-50, -10)
            elif particle['x'].x < -50:
                particle['x'].x = SCREEN_WIDTH + random.randint(10, 50)
                
            if particle['x'].y > SCREEN_HEIGHT + 50:
                particle['x'].y = random.randint(-100, -10)
                particle['x'].x = random.randint(0, SCREEN_WIDTH)
                particle['speed'].y = random.uniform(1, 3)
    
    def draw_bitcoin_symbol(self, surface, x, y, size, rotation):
        # Draw a simple bitcoin "B" symbol
        font = pygame.font.Font(None, size)
        text = font.render("₿", True, GOLD)
        
        # Rotate the text
        rotated = pygame.transform.rotate(text, rotation)
        rect = rotated.get_rect(center=(x, y))
        surface.blit(rotated, rect)
    
    def draw_gradient_background(self):
        # Create a gradient background
        for y in range(SCREEN_HEIGHT):
            color_ratio = y / SCREEN_HEIGHT
            r = int(DARK_BLUE[0] * (1 - color_ratio) + BLACK[0] * color_ratio)
            g = int(DARK_BLUE[1] * (1 - color_ratio) + BLACK[1] * color_ratio)
            b = int(DARK_BLUE[2] * (1 - color_ratio) + BLACK[2] * color_ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def draw_title(self):
        # Animated title with glow effect
        self.time += 0.02
        
        # Create glow effect
        glow_size = abs(math.sin(self.time)) * 5 + 2
        
        # Draw title shadow
        shadow_text = self.title_font.render("Bitcoin Puzzle", True, BLACK)
        shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH // 2 + 3, 150 + 3))
        self.screen.blit(shadow_text, shadow_rect)
        
        # Draw main title
        title_text = self.title_font.render("Bitcoin Puzzle", True, GOLD)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        
        # Draw glow
        for i in range(int(glow_size)):
            glow_alpha = 50 - i * 10
            if glow_alpha > 0:
                glow_surf = self.title_font.render("Bitcoin Puzzle", True, ORANGE)
                glow_surf.set_alpha(glow_alpha)
                glow_rect = glow_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
                self.screen.blit(glow_surf, glow_rect)
        
        self.screen.blit(title_text, title_rect)
        
        # Draw "Adventures" subtitle
        subtitle_text = self.subtitle_font.render("Adventures", True, LIGHT_BLUE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle_text, subtitle_rect)
        
    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.start_button.rect.collidepoint(mouse_pos):
                        self.game_started = True
                        self.running = False
                        if self.music_loaded:
                            pygame.mixer.music.stop()
                        return True
                    
                    if self.exit_button.rect.collidepoint(mouse_pos):
                        self.running = False
                        if self.music_loaded:
                            pygame.mixer.music.stop()
                        pygame.quit()
                        sys.exit()
            
            # Update
            self.start_button.update(mouse_pos)
            self.exit_button.update(mouse_pos)
            self.update_particles()
            
            # Draw
            self.draw_gradient_background()
            
            # Draw particles
            for particle in self.particles:
                self.draw_bitcoin_symbol(
                    self.screen,
                    int(particle['x'].x),
                    int(particle['x'].y),
                    particle['size'],
                    particle['rotation']
                )
            
            self.draw_title()
            self.start_button.draw(self.screen)
            self.exit_button.draw(self.screen)
            
            # Draw music status
            if not self.music_loaded:
                font = pygame.font.Font(None, 20)
                text = font.render("Add menu_music.mp3 for background music", True, WHITE)
                self.screen.blit(text, (10, SCREEN_HEIGHT - 25))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        return self.game_started

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bitcoin Puzzle Adventures")
        self.clock = pygame.time.Clock()
        self.running = True
        self.lastbin = ''
        self.lastAddress = ''
        self.lastPrivate = 0
        self.puzzle_solved = {}  # Track which puzzles are solved
        self.winning_patterns = {}  # Store the winning binary patterns
        
    def screen_to_iso(self, x, y):
        """Convert screen coordinates to isometric coordinates"""
        iso_x = (x - y) * 2
        iso_y = (x + y)
        return iso_x, iso_y
    
    def iso_to_screen(self, iso_x, iso_y):
        """Convert isometric coordinates to screen coordinates"""
        x = (iso_x / 2 + iso_y) / 2
        y = (iso_y - iso_x / 2) / 2
        return x, y
        
    def draw_iso_tile(self, grid_x, grid_y, color, highlight=False, camera_x=0, camera_y=0):
        """Draw an isometric tile at grid position with camera offset"""
        tile_width = 60
        tile_height = 30
        
        # Calculate screen position with camera offset
        screen_x = (grid_x - grid_y) * (tile_width // 2) + SCREEN_WIDTH // 2 - camera_x
        screen_y = (grid_x + grid_y) * (tile_height // 2) + 150 - camera_y
        
        # Only draw if tile is visible on screen
        if -tile_width <= screen_x <= SCREEN_WIDTH + tile_width and -tile_height <= screen_y <= SCREEN_HEIGHT + tile_height:
            # Define tile vertices
            vertices = [
                (screen_x, screen_y),
                (screen_x + tile_width // 2, screen_y + tile_height // 2),
                (screen_x, screen_y + tile_height),
                (screen_x - tile_width // 2, screen_y + tile_height // 2)
            ]
            
            # Draw tile
            if highlight:
                pygame.draw.polygon(self.screen, LIGHT_BLUE, vertices)
                pygame.draw.polygon(self.screen, WHITE, vertices, 3)
            else:
                pygame.draw.polygon(self.screen, color, vertices)
                pygame.draw.polygon(self.screen, DARK_GOLD, vertices, 2)
        
        return screen_x, screen_y + tile_height // 2
    
    def get_tile_from_mouse(self, mouse_x, mouse_y, grid_width, grid_height, camera_x=0, camera_y=0):
        """Convert mouse position to grid coordinates with camera offset"""
        tile_width = 60
        tile_height = 30
        
        # Offset mouse position relative to grid center and add camera offset
        offset_x = mouse_x - SCREEN_WIDTH // 2 + camera_x
        offset_y = mouse_y - 150 + camera_y
        
        # Convert to grid coordinates (approximate)
        grid_x = (offset_x / (tile_width // 2) + offset_y / (tile_height // 2)) / 2
        grid_y = (offset_y / (tile_height // 2) - offset_x / (tile_width // 2)) / 2
        
        # Round to nearest integer and check bounds
        grid_x = round(grid_x)
        grid_y = round(grid_y)
        
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            return grid_x, grid_y
        return None, None
    
    def draw_player(self, grid_x, grid_y, bounce_offset=0, camera_x=0, camera_y=0):
        """Draw the player as a ball at grid position with camera offset"""
        tile_width = 60
        tile_height = 30
        
        # Calculate screen position with camera offset
        screen_x = (grid_x - grid_y) * (tile_width // 2) + SCREEN_WIDTH // 2 - camera_x
        screen_y = (grid_x + grid_y) * (tile_height // 2) + 150 - 20 - bounce_offset - camera_y
        
        # Draw shadow
        shadow_y = (grid_x + grid_y) * (tile_height // 2) + 150 + tile_height // 2 - camera_y
        pygame.draw.ellipse(self.screen, (0, 0, 0, 128), 
                          (screen_x - 15, shadow_y - 5, 30, 10))
        
        # Draw ball with gradient effect
        pygame.draw.circle(self.screen, GOLD, (int(screen_x), int(screen_y)), 15)
        pygame.draw.circle(self.screen, ORANGE, (int(screen_x), int(screen_y)), 15, 3)
        pygame.draw.circle(self.screen, WHITE, (int(screen_x - 5), int(screen_y - 5)), 5)
    
    def draw_stat_bar(self, x, y, width, height, current, maximum, color, bg_color):
        """Draw a stat bar (health, mana, exp)"""
        # Background
        pygame.draw.rect(self.screen, bg_color, (x, y, width, height))
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2)
        
        # Fill
        fill_width = int((current / maximum) * width)
        if fill_width > 0:
            pygame.draw.rect(self.screen, color, (x, y, fill_width, height))
        
        # Text
        font = pygame.font.Font(None, 16)
        text = font.render(f"{current}/{maximum}", True, WHITE)
        text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text, text_rect)
    
    def draw_player_stats(self, player_stats):
        """Draw player stats menu in top left"""
        # Background panel
        panel_x, panel_y = 10, 10
        panel_width, panel_height = 200, 180
        
        # Semi-transparent background
        panel_surface = pygame.Surface((panel_width, panel_height))
        panel_surface.set_alpha(220)
        panel_surface.fill((20, 20, 40))
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Border
        pygame.draw.rect(self.screen, GOLD, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Fonts
        title_font = pygame.font.Font(None, 24)
        stat_font = pygame.font.Font(None, 20)
        
        # Starting position for content
        content_x = panel_x + 10
        content_y = panel_y + 10
        
        # Level
        level_text = title_font.render(f"Level {player_stats['level']}", True, GOLD)
        self.screen.blit(level_text, (content_x, content_y))
        content_y += 30
        
        # Health bar
        health_label = stat_font.render("Health:", True, WHITE)
        self.screen.blit(health_label, (content_x, content_y))
        content_y += 20
        self.draw_stat_bar(content_x, content_y, 180, 20, 
                          player_stats['health'], player_stats['max_health'],
                          (255, 0, 0), (100, 0, 0))
        content_y += 25
        
        # Mana bar
        mana_label = stat_font.render("Mana:", True, WHITE)
        self.screen.blit(mana_label, (content_x, content_y))
        content_y += 20
        self.draw_stat_bar(content_x, content_y, 180, 20,
                          player_stats['mana'], player_stats['max_mana'],
                          (0, 100, 255), (0, 0, 100))
        content_y += 25
        
        # Damage and Armor
        damage_text = stat_font.render(f"Damage: {player_stats['damage']}", True, WHITE)
        self.screen.blit(damage_text, (content_x, content_y))
        
        armor_text = stat_font.render(f"Armor: {player_stats['armor']}", True, WHITE)
        armor_rect = armor_text.get_rect(right=panel_x + panel_width - 10, y=content_y)
        self.screen.blit(armor_text, armor_rect)
        content_y += 25
        
        # Experience bar
        exp_label = stat_font.render("Experience:", True, WHITE)
        self.screen.blit(exp_label, (content_x, content_y))
        content_y += 20
        self.draw_stat_bar(content_x, content_y, 180, 20,
                          player_stats['experience'], player_stats['exp_to_next_level'],
                          (255, 215, 0), (100, 100, 0))
                          
    def draw_npc(self, grid_x, grid_y, camera_x=0, camera_y=0):
        """Draw an NPC as a standing character on the grid"""
        tile_width = 60
        tile_height = 30
        
        # Convert grid coordinates to screen coordinates
        screen_x = (grid_x - grid_y) * (tile_width // 2) + SCREEN_WIDTH // 2 - camera_x
        screen_y = (grid_x + grid_y) * (tile_height // 2) + 150 - camera_y
        
        # Draw shadow
        shadow_y = screen_y + tile_height // 2
        pygame.draw.ellipse(self.screen, (0, 0, 0, 128), 
                            (screen_x - 12, shadow_y - 4, 24, 8))
        
        # Draw NPC (simple character shape)
        pygame.draw.rect(self.screen, (150, 75, 0), (screen_x - 8, screen_y - 28, 16, 28))  # body
        pygame.draw.circle(self.screen, (255, 220, 180), (int(screen_x), int(screen_y - 35)), 8)  # head
        
        # Optional sparkle or animation effect
        glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 100, 80), (10, 10), 10)
        self.screen.blit(glow, (screen_x - 10, screen_y - 45))
            
    def draw_portal(self, grid_x, grid_y, portal_type, camera_x=0, camera_y=0):
        """Draw a portal with unique appearance based on type"""
        tile_width = 60
        tile_height = 30
        
        # Calculate screen position with camera offset
        screen_x = (grid_x - grid_y) * (tile_width // 2) + SCREEN_WIDTH // 2 - camera_x
        screen_y = (grid_x + grid_y) * (tile_height // 2) + 150 - camera_y
        
        portal_time = pygame.time.get_ticks() / 1000.0
        
        # Different colors for different portal types
        portal_colors = {
            'puzzle17': (50, 150, 255),    # Bright Blue
            'puzzle21': (50, 255, 50),     # Bright Green
            'puzzle25': (200, 50, 255),    # Bright Purple
            'puzzle73': (255, 100, 0),     # Bright Orange
            'main': (0, 200, 255)          # Bright Blue
        }
        
        color = portal_colors.get(portal_type, (255, 255, 255))
        
        # Animated portal size
        portal_size = int(15 + 8 * abs(math.sin(portal_time * 2)))
        
        # Draw outer glow
        glow_size = portal_size + 10
        glow_color = tuple(c // 3 for c in color)
        pygame.draw.circle(self.screen, glow_color, (int(screen_x), int(screen_y + tile_height // 4)), glow_size)
        
        # Draw main portal circle
        pygame.draw.circle(self.screen, WHITE, (int(screen_x), int(screen_y + tile_height // 4)), portal_size + 2)
        pygame.draw.circle(self.screen, color, (int(screen_x), int(screen_y + tile_height // 4)), portal_size)
        
        # Draw inner swirl
        inner_size = portal_size - 5
        inner_rotation = portal_time * 3
        for i in range(3):
            angle = inner_rotation + (i * 2 * math.pi / 3)
            inner_x = screen_x + math.cos(angle) * (inner_size // 2)
            inner_y = screen_y + tile_height // 4 + math.sin(angle) * (inner_size // 2)
            pygame.draw.circle(self.screen, WHITE, (int(inner_x), int(inner_y)), 3)
        
        # Draw portal label
        portal_font = pygame.font.Font(None, 24)
        portal_text = portal_font.render(portal_type.upper(), True, WHITE)
        text_rect = portal_text.get_rect(center=(screen_x, screen_y - 15))
        
        # Add background to text for readability
        text_bg = pygame.Surface((text_rect.width + 10, text_rect.height + 4))
        text_bg.set_alpha(128)
        text_bg.fill((0, 0, 0))
        self.screen.blit(text_bg, (text_rect.x - 5, text_rect.y - 2))
        self.screen.blit(portal_text, text_rect)
            
    def draw_dialog(self, message):
        """Draw a dialog box with the given message"""
        font = pygame.font.Font(None, 24)
        padding = 10
        max_width = 500
        
        # Word wrap
        words = message.split(' ')
        lines = []
        current_line = ''
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Calculate height
        line_height = font.get_height()
        box_height = line_height * len(lines) + padding * 2
        box_width = max(font.size(line)[0] for line in lines) + padding * 2
        
        # Box position
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = SCREEN_HEIGHT - box_height - 60
        
        # Background
        dialog_surface = pygame.Surface((box_width, box_height))
        dialog_surface.set_alpha(220)
        dialog_surface.fill((30, 30, 60))
        self.screen.blit(dialog_surface, (box_x, box_y))
        
        # Border
        pygame.draw.rect(self.screen, GOLD, (box_x, box_y, box_width, box_height), 2)
        
        # Draw text lines
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, WHITE)
            self.screen.blit(text_surface, (box_x + padding, box_y + padding + i * line_height))
            
    def start_game_music(self):
        """Start background music for the game"""
        try:
            pygame.mixer.music.load("game_music.mp3")
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)  # Loop forever
            return True
        except:
            print("Note: game_music.mp3 not found. Add your own MP3 file to enable game music.")
            return False
    
    def game_screen(self):
        # Start game background music
        game_music_loaded = self.start_game_music()
        
        # Game screen with isometric grid
        font_title = pygame.font.Font(None, 48)
        font_text = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 18)
        
        # Level system with 3 different puzzle realms
        current_level = 'main'
        
        # Grid settings per level
        level_grids = {
            'main': {'width': 8, 'height': 9},
            'puzzle17': {'width': 4, 'height': 4},
            'puzzle21': {'width': 4, 'height': 5},
            'puzzle25': {'width': 6, 'height': 4},
            'puzzle73': {'width': 9, 'height': 8}
        }
        
        # Get current grid dimensions
        grid_width = level_grids[current_level]['width']
        grid_height = level_grids[current_level]['height']
        
        player_x, player_y = grid_width // 2, grid_height // 2  # Start near center
        target_x, target_y = player_x, player_y
        move_progress = 1.0
        bounce_time = 0
        has_toggled_current_tile = True  # Track if we've already toggled the current tile
        
        level_names = {
            'main': 'Central Hub',
            'puzzle17': 'Puzzle 17', 
            'puzzle21': 'Puzzle 21',
            'puzzle25': 'Puzzle 25',
            'puzzle73': 'Puzzle 73'
        }
        
        # Portal positions for each level (4 portals in main hub)
        portal_positions = {
            'main': [
                {'x': 1, 'y': 7, 'type': 'puzzle17', 'dest': 'puzzle17'},
                {'x': 1, 'y': 1, 'type': 'puzzle21', 'dest': 'puzzle21'},
                {'x': 6, 'y': 1, 'type': 'puzzle25', 'dest': 'puzzle25'},
                {'x': 6, 'y': 7, 'type': 'puzzle73', 'dest': 'puzzle73'}
            ],
            'puzzle17': [{'x': 2, 'y': 3, 'type': 'main', 'dest': 'main'}],
            'puzzle21': [{'x': 2, 'y': 4, 'type': 'main', 'dest': 'main'}],
            'puzzle25': [{'x': 3, 'y': 3, 'type': 'main', 'dest': 'main'}],
            'puzzle73': [{'x': 4, 'y': 7, 'type': 'main', 'dest': 'main'}]
        }
        
        # Initialize tile states for multiple levels
        all_tile_states = {}
        for level in ['main', 'puzzle17','puzzle21', 'puzzle25', 'puzzle73']:
            level_grid = level_grids[level]
            all_tile_states[level] = [[0 for _ in range(level_grid['width'])] for _ in range(level_grid['height'])]
        
        # Current level tile states
        tile_states = all_tile_states[current_level]
        
        # Camera settings
        camera_x, camera_y = 0, 0
        target_camera_x, target_camera_y = 0, 0
        camera_smoothing = 0.1
        tile_width = 60
        tile_height = 30
        
        # Player stats
        player_stats = {
            'level': 1,
            'health': 85,
            'max_health': 100,
            'mana': 75,
            'max_mana': 100,
            'damage': 10,
            'armor': 5,
            'experience': 350,
            'exp_to_next_level': 1000
        }
        
        # NPC system for each level
        npc_positions = {
            'main': {'x': 4, 'y': 4, 'active': True, 'message': "Welcome to the Central Hub! Use the four portals to solve Bitcoin puzzles. Each puzzle has a different difficulty level! and remember 'A few words about the puzzle. There is no pattern. It is just consecutive keys from a deterministic wallet (masked with leading 000...0001 to set difficulty). It is simply a crude measuring instrument, of the cracking strength of the community.'"},
            'puzzle17': {'x': 1, 'y': 1, 'active': True, 'message': "This is Puzzle 17! A compact 4x4 grid with 16 tiles. Perfect square formation for balanced key exploration."},
            'puzzle21': {'x': 1, 'y': 2, 'active': True, 'message': "This is Puzzle 21! A 4x5 grid with 20 tiles. Your binary patterns here represent smaller private key ranges."},
            'puzzle25': {'x': 4, 'y': 1, 'active': True, 'message': "Welcome to Puzzle 25! This 6x4 grid has 24 tiles total. Medium difficulty with more pattern combinations."},
            'puzzle73': {'x': 7, 'y': 3, 'active': True, 'message': "You've reached Puzzle 73! This massive 9x8 grid contains 72 tiles. The ultimate challenge with enormous key spaces!"}
        }
        
        # Dialog system
        show_dialog = False
        dialog_message = ""
        dialog_timer = 0
        dialog_duration = 720  # frames (12 seconds at 60 FPS)
        dialog_just_triggered = False  # Prevent immediate closing
        dialog_min_display_time = 300  # 5 seconds at 60 FPS
        
        # Victory celebration system
        show_victory = False
        victory_message = ""
        victory_particles = []
        victory_just_triggered = False  # Prevent immediate closing
        
        def get_binary_string():
            """Convert tile states to binary string"""
            binary = ""
            for row in tile_states:
                for tile in row:
                    binary += str(tile)
            return binary
        
        def create_victory_particles():
            """Create celebration particles when puzzle is solved"""
            import random
            particles = []
            for _ in range(100):
                particles.append({
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(0, SCREEN_HEIGHT),
                    'vx': random.uniform(-5, 5),
                    'vy': random.uniform(-8, -2),
                    'life': random.randint(60, 180),
                    'color': random.choice([GOLD, ORANGE, WHITE, (255, 255, 0)])
                })
            return particles
        
        def update_victory_particles(particles):
            """Update victory celebration particles"""
            for particle in particles[:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vy'] += 0.2  # gravity
                particle['life'] -= 1
                
                if particle['life'] <= 0 or particle['y'] > SCREEN_HEIGHT:
                    particles.remove(particle)
        
        def draw_victory_particles(particles):
            """Draw victory celebration particles"""
            for particle in particles:
                alpha = min(255, particle['life'] * 3)
                size = max(1, particle['life'] // 20)
                pygame.draw.circle(self.screen, particle['color'], 
                                 (int(particle['x']), int(particle['y'])), size)
        
        def get_level_colors(level):
            """Get base colors for different levels"""
            level_themes = {
                'main': (DARK_BLUE, (0, 0, 100)),
                'puzzle17': ((20, 60, 80), (10, 40, 60)),  # Blue theme for puzzle 17
                'puzzle21': ((20, 80, 20), (10, 60, 10)),  # Green theme for puzzle 21
                'puzzle25': ((80, 20, 80), (60, 10, 60)),  # Purple theme for puzzle 25
                'puzzle73': ((80, 40, 0), (100, 50, 0))    # Orange theme for puzzle 73
            }
            return level_themes.get(level, (DARK_BLUE, (0, 0, 100)))
        
        def draw_tile_with_state(x, y, base_color, is_lit, highlight=False, is_portal=False, portal_type=None, is_frozen=False):
            """Draw tile with lighting state and portal"""
            if is_portal:
                # Portal tile gets special handling
                self.draw_portal(x, y, portal_type, camera_x, camera_y)
                return
            elif is_lit:
                # Light tile - bright colors based on level
                if current_level == 'puzzle17':
                    color = (100, 180, 255) if (x + y) % 2 == 0 else (150, 200, 255)
                elif current_level == 'puzzle21':
                    color = (100, 255, 100) if (x + y) % 2 == 0 else (150, 255, 150)
                elif current_level == 'puzzle25':
                    color = (200, 100, 255) if (x + y) % 2 == 0 else (255, 150, 255)
                elif current_level == 'puzzle73':
                    color = (255, 150, 50) if (x + y) % 2 == 0 else (255, 200, 100)
                else:
                    color = GOLD if (x + y) % 2 == 0 else ORANGE
                
                # If puzzle is solved, add golden glow to all lit tiles
                if is_frozen:
                    r, g, b = color
                    color = (min(255, r + 50), min(255, g + 50), min(255, b + 50))
            else:
                # Dark tile - normal colors
                color = base_color
                
                # If puzzle is solved, lighten dark tiles too
                if is_frozen:
                    r, g, b = color
                    color = (min(255, r + 30), min(255, g + 30), min(255, b + 30))
            
            self.draw_iso_tile(x, y, color, highlight=highlight and not is_frozen, 
                             camera_x=camera_x, camera_y=camera_y)
            
            # Draw frozen indicator
            if is_frozen:
                tile_width = 60
                tile_height = 30
                screen_x = (x - y) * (tile_width // 2) + SCREEN_WIDTH // 2 - camera_x
                screen_y = (x + y) * (tile_height // 2) + 150 - camera_y
                
                # Draw small sparkle effect
                sparkle_time = pygame.time.get_ticks() / 200.0
                if int(sparkle_time + x + y) % 4 == 0:  # Staggered sparkles
                    pygame.draw.circle(self.screen, WHITE, (int(screen_x), int(screen_y + 10)), 3)
                    pygame.draw.circle(self.screen, GOLD, (int(screen_x), int(screen_y + 10)), 2)
        
        def check_portal_collision(player_pos):
            """Check if player is on a portal and return destination"""
            px, py = int(player_pos[0]), int(player_pos[1])
            portals = portal_positions.get(current_level, [])
            
            for portal in portals:
                if px == portal['x'] and py == portal['y']:
                    return portal['dest']
            return None
        
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if show_victory:
                            # Close victory window
                            show_victory = False
                            victory_particles.clear()
                        elif show_dialog:
                            # Close dialog only if it's been showing for at least 5 seconds
                            if dialog_timer <= (dialog_duration - dialog_min_display_time):
                                show_dialog = False
                                dialog_timer = 0
                        else:
                            if game_music_loaded:
                                pygame.mixer.music.stop()
                            return True  # Return to menu
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if show_victory and not victory_just_triggered:
                        # Close victory window on any click (but not immediately after it appears)
                        show_victory = False
                        victory_particles.clear()
                    elif show_dialog and not dialog_just_triggered:
                        # Close dialog on any click, but only if it's been showing for at least 5 seconds
                        if dialog_timer <= (dialog_duration - dialog_min_display_time):
                            show_dialog = False
                            dialog_timer = 0
                    elif not show_victory:
                        # Check which tile was clicked with camera offset
                        clicked_x, clicked_y = self.get_tile_from_mouse(
                            mouse_pos[0], mouse_pos[1], grid_width, grid_height, camera_x, camera_y
                        )
                        if clicked_x is not None and clicked_y is not None:
                            # Check if clicking on NPC
                            npc_data = npc_positions.get(current_level, {})
                            if (npc_data.get('active') and 
                                clicked_x == npc_data['x'] and 
                                clicked_y == npc_data['y']):
                                # Show dialog and deactivate NPC
                                show_dialog = True
                                dialog_just_triggered = True  # Prevent immediate closing
                                dialog_message = npc_data['message']
                                dialog_timer = dialog_duration
                                npc_data['active'] = False
                            else:
                                # Allow movement even in solved puzzles, but only prevent tile toggling
                                if (not show_dialog and
                                    (clicked_x != int(player_x) or clicked_y != int(player_y))):
                                    # Set new target position
                                    target_x, target_y = clicked_x, clicked_y
                                    move_progress = 0.0
                                    has_toggled_current_tile = False  # Reset toggle flag for new movement
                            
                            # Simulate gaining some exp for movement (for demo)
                            player_stats['experience'] += 10
                            if player_stats['experience'] >= player_stats['exp_to_next_level']:
                                player_stats['level'] += 1
                                player_stats['experience'] = 0
                                player_stats['exp_to_next_level'] = player_stats['level'] * 1000
                                player_stats['max_health'] += 10
                                player_stats['max_mana'] += 10
                                player_stats['damage'] += 2
                                player_stats['armor'] += 1
                                player_stats['health'] = player_stats['max_health']
                                player_stats['mana'] = player_stats['max_mana']
            
            # Update highlighted tile based on mouse position
            highlighted_tile = self.get_tile_from_mouse(mouse_pos[0], mouse_pos[1], grid_width, grid_height, camera_x, camera_y)
            
            # Update dialog timer
            if show_dialog and dialog_timer > 0:
                dialog_timer -= 1
                # Reset the dialog trigger flag after one frame
                if dialog_just_triggered:
                    dialog_just_triggered = False
                if dialog_timer <= 0:
                    show_dialog = False
            
            # Update victory particles and reset victory trigger flag
            if show_victory:
                update_victory_particles(victory_particles)
                # Reset the victory trigger flag after one frame
                if victory_just_triggered:
                    victory_just_triggered = False
            
            # Update player movement
            if move_progress < 1.0:
                move_progress += 0.1
                if move_progress > 1.0:
                    move_progress = 1.0
                
                # Interpolate position
                player_x = player_x + (target_x - player_x) * move_progress
                player_y = player_y + (target_y - player_y) * move_progress
            else:
                player_x, player_y = target_x, target_y
                current_x, current_y = int(player_x), int(player_y)
                
                # Check for portal teleportation
                portal_dest = check_portal_collision((player_x, player_y))
                if portal_dest:
                    # Save current level's tile states
                    all_tile_states[current_level] = tile_states
                    
                    # Move to destination level
                    current_level = portal_dest
                    
                    # Update grid dimensions for new level
                    grid_width = level_grids[current_level]['width']
                    grid_height = level_grids[current_level]['height']
                    
                    tile_states = all_tile_states[current_level]
                    
                    # Teleport player to center of new level
                    player_x, player_y = float(grid_width // 2), float(grid_height // 2)
                    target_x, target_y = player_x, player_y
                    has_toggled_current_tile = True
                    
                    # Reset camera for smooth transition
                    camera_x, camera_y = 0, 0
                    
                    # Gain bonus experience for changing levels
                    player_stats['experience'] += 50
                else:
                    # Toggle tile state only once when player reaches a non-portal tile
                    # But only if puzzle is not already solved
                    if (not has_toggled_current_tile and 
                        not self.puzzle_solved.get(current_level, False)):
                        if 0 <= current_x < grid_width and 0 <= current_y < grid_height:
                            tile_states[current_y][current_x] = 1 - tile_states[current_y][current_x]
                            has_toggled_current_tile = True
            
            # Update camera to follow player
            player_screen_x = (player_x - player_y) * (tile_width // 2)
            player_screen_y = (player_x + player_y) * (tile_height // 2)
            
            # Calculate target camera position to center player
            target_camera_x = player_screen_x
            target_camera_y = player_screen_y - 150
            
            # Smooth camera movement
            camera_x += (target_camera_x - camera_x) * camera_smoothing
            camera_y += (target_camera_y - camera_y) * camera_smoothing
            
            # Update bounce animation
            bounce_time += 0.1
            bounce_offset = abs(math.sin(bounce_time)) * 5 if move_progress < 1.0 else 0
            
            # Draw level-appropriate background
            level_color1, level_color2 = get_level_colors(current_level)
            for y in range(SCREEN_HEIGHT):
                color_ratio = y / SCREEN_HEIGHT
                r = int(level_color1[0] * (1 - color_ratio) + level_color2[0] * color_ratio)
                g = int(level_color1[1] * (1 - color_ratio) + level_color2[1] * color_ratio)
                b = int(level_color1[2] * (1 - color_ratio) + level_color2[2] * color_ratio)
                pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
            
            # Draw title with level indicator
            level_display_name = level_names.get(current_level, current_level.title())
            title_text = font_title.render(f"Bitcoin Puzzle - {level_display_name}", True, GOLD)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(title_text, title_rect)
            
            # Draw isometric grid with camera offset and lighting states
            base_color1, base_color2 = get_level_colors(current_level)
            puzzle_is_solved = self.puzzle_solved.get(current_level, False)
            
            for y in range(grid_height):
                for x in range(grid_width):
                    # Base color for checkerboard pattern
                    base_color = base_color1 if (x + y) % 2 == 0 else base_color2
                    is_highlighted = (x, y) == highlighted_tile and not puzzle_is_solved
                    is_lit = tile_states[y][x] == 1
                    
                    # Check if this tile is a portal
                    is_portal = False
                    portal_type = None
                    portals = portal_positions.get(current_level, [])
                    for portal in portals:
                        if x == portal['x'] and y == portal['y']:
                            is_portal = True
                            portal_type = portal['type']
                            break
                    
                    draw_tile_with_state(x, y, base_color, is_lit, 
                                       highlight=is_highlighted, is_portal=is_portal, 
                                       portal_type=portal_type, is_frozen=puzzle_is_solved)
            
            # Draw player with camera offset
            self.draw_player(player_x, player_y, bounce_offset, camera_x, camera_y)
            
            # Draw NPC if active
            npc_data = npc_positions.get(current_level, {})
            if npc_data.get('active'):
                self.draw_npc(npc_data['x'], npc_data['y'], camera_x, camera_y)
            
            # Draw victory celebration if active
            if show_victory:
                draw_victory_particles(victory_particles)
                
                # Draw victory message
                victory_lines = victory_message.split('\n')
                victory_font = pygame.font.Font(None, 36)
                victory_small_font = pygame.font.Font(None, 24)
                
                # Calculate total height
                total_height = len(victory_lines) * 30 + 40
                box_width = 600
                box_height = total_height
                
                # Draw victory box
                box_x = SCREEN_WIDTH // 2 - box_width // 2
                box_y = SCREEN_HEIGHT // 2 - box_height // 2
                
                # Background with alpha
                victory_surface = pygame.Surface((box_width, box_height))
                victory_surface.set_alpha(240)
                victory_surface.fill((20, 50, 20))
                self.screen.blit(victory_surface, (box_x, box_y))
                
                # Golden border
                pygame.draw.rect(self.screen, GOLD, (box_x, box_y, box_width, box_height), 4)
                
                # Draw text lines
                y_offset = 20
                for i, line in enumerate(victory_lines):
                    if '🎉' in line or 'CONGRATULATIONS' in line:
                        text_surface = victory_font.render(line, True, GOLD)
                    elif 'Winning Key:' in line or 'Address:' in line:
                        text_surface = victory_small_font.render(line, True, WHITE)
                    else:
                        text_surface = victory_small_font.render(line, True, LIGHT_BLUE)
                    
                    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, box_y + y_offset))
                    self.screen.blit(text_surface, text_rect)
                    y_offset += 30
                
                # Add instruction text at bottom of victory box
                instruction_text = victory_small_font.render("Press ESC or click anywhere to close", True, WHITE)
                instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + box_height - 20))
                self.screen.blit(instruction_text, instruction_rect)
            
            # Draw dialog if active (but not if victory is showing)
            elif show_dialog:
                self.draw_dialog(dialog_message)
                
                # Add instruction text for closing dialog
                font_small = pygame.font.Font(None, 18)
                # Show different instruction based on whether dialog can be closed yet
                remaining_time = dialog_timer - (dialog_duration - dialog_min_display_time)
                if remaining_time > 0:
                    seconds_left = int(remaining_time / 60) + 1
                    instruction_text = font_small.render(f"Dialog will be closable in {seconds_left} seconds...", True, ORANGE)
                else:
                    instruction_text = font_small.render("Press ESC or click anywhere to close", True, WHITE)
                
                instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
                
                # Add background to instruction text for readability
                text_bg = pygame.Surface((instruction_rect.width + 10, instruction_rect.height + 4))
                text_bg.set_alpha(128)
                text_bg.fill((0, 0, 0))
                self.screen.blit(text_bg, (instruction_rect.x - 5, instruction_rect.y - 2))
                self.screen.blit(instruction_text, instruction_rect)
            
            # Draw current position indicator
            pos_text = font_text.render(f"Position: ({int(player_x)}, {int(player_y)})", True, WHITE)
            pos_rect = pos_text.get_rect(topright=(SCREEN_WIDTH - 10, 10))
            self.screen.blit(pos_text, pos_rect)
            
            # Draw binary string info and check for target
            binary_string = get_binary_string()
            lit_count = binary_string.count('1')
            total_tiles = grid_width * grid_height
            
            # Only process binary if puzzle is not solved and we're in a puzzle level
            current_target = TARGETS.get(current_level)
            puzzle_is_solved = self.puzzle_solved.get(current_level, False)
            
            if current_target and not puzzle_is_solved:
                bin2 = binary_string
                if bin2 != self.lastbin:
                    self.lastbin = bin2
                    size = len(bin2)
                    hexSize = size // 4
                    target_found = False
                    
                    for inv in range(2):
                        for z in range(2):
                            for y in range(size):
                                pp = int(bin2, 2)
                                hex2 = hex(pp)[2:].zfill(hexSize)
                                for x in range(16):
                                    p = int('1' + hex2, 16)
                                    address = ice.privatekey_to_address(0, True, p)
                                    
                                    if y == 0 and z == 0 and inv == 0 and x == 0:
                                        print(bin2 + ' - ' + hex(p)[2:] + ' -> ' + address)
                                        self.lastAddress = address
                                        self.lastPrivate = p
                                    
                                    if address == current_target: 
                                        print(f"🎉 PUZZLE {current_level.upper()} SOLVED! 🎉")
                                        print(hex(p)[2:] + ' -> ' + address)
                                        
                                        # Mark puzzle as solved
                                        self.puzzle_solved[current_level] = True
                                        self.winning_patterns[current_level] = binary_string
                                        
                                        # Show victory message
                                        show_victory = True
                                        victory_just_triggered = True  # Prevent immediate closing
                                        victory_message = f"🎉 CONGRATULATIONS! 🎉\n\nYou solved {current_level.upper()}!\n\nWinning Key: {hex(p)[2:]}\nAddress: {address}\n\nAll tiles are now frozen in this room!"
                                        victory_particles = create_victory_particles()
                                        
                                        # Save to file
                                        with open('found.txt', 'a') as file:
                                            file.write(f"{current_level.upper()} SOLVED: {hex(p)[2:]} -> {address}\n")
                                        
                                        target_found = True
                                        break
                                    hex2 = rotate_hex(hex2)
                                if target_found:
                                    break
                                bin2 = shift_left(bin2, 1)
                            if target_found:
                                break
                            bin2 = bin2[::-1]
                        if target_found:
                            break
                        bin2 = inverse(bin2)
                        if target_found:
                            break
            
            # Display current address info only for puzzle levels (not main hub)
            if hasattr(self, 'lastAddress') and self.lastAddress and current_level != 'main':
                address_info = font_text.render(hex(self.lastPrivate)[2:] + ' -> ' + self.lastAddress, True, WHITE)
                self.screen.blit(address_info, (10, 125))
            
            # Binary info box
            info_y = 40
            binary_info = font_text.render(f"Lit Tiles: {lit_count}/{total_tiles}", True, WHITE)
            self.screen.blit(binary_info, (SCREEN_WIDTH - 150, info_y))
            
            # Show grid dimensions
            info_y += 50
            grid_info = font_text.render(f"Grid: {grid_width}x{grid_height}", True, WHITE)
            self.screen.blit(grid_info, (10, info_y))
            
            # Show current target address for this puzzle
            current_target = TARGETS.get(current_level)
            puzzle_is_solved = self.puzzle_solved.get(current_level, False)
            
            if current_target:
                info_y += 75
                if puzzle_is_solved:
                    target_text = font_small.render(f"Target: {current_target} ✅ SOLVED!", True, (0, 255, 0))
                else:
                    target_text = font_small.render(f"Target: {current_target}", True, LIGHT_BLUE)
                self.screen.blit(target_text, (10, info_y))
            
            # Show puzzle status
            if puzzle_is_solved:
                info_y += 50
                status_text = font_small.render("🔒 PUZZLE SOLVED - TILES FROZEN", True, GOLD)
                self.screen.blit(status_text, (SCREEN_WIDTH - 750, info_y))
            
            # Draw portal information
            portals = portal_positions.get(current_level, [])
            if portals:
                info_y = SCREEN_HEIGHT - SCREEN_HEIGHT // 3
                portal_info = font_small.render("Portals:", True, (100, 255, 100))
                self.screen.blit(portal_info, (10, info_y))
                info_y += 20
                
                for portal in portals:
                    portal_text = f"• {portal['type'].title()} at ({portal['x']}, {portal['y']})"
                    portal_render = font_small.render(portal_text, True, WHITE)
                    self.screen.blit(portal_render, (15, info_y))
                    info_y += 18
            
            # Draw instructions
            if not show_victory:
                instruction_text = font_text.render("Click to move and toggle lights | Use portals to travel | ESC to return", True, LIGHT_BLUE)
                instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
                self.screen.blit(instruction_text, instruction_rect)
            
            # Draw music status if no game music
            if not game_music_loaded:
                music_text = font_small.render("Add game_music.mp3 for background music", True, WHITE)
                self.screen.blit(music_text, (10, 10))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        return False
        
    def run(self):
        while self.running:
            # Show main menu
            menu = MainMenu(self.screen)
            start_game = menu.run()
            
            if start_game:
                # Show game screen
                show_menu_again = self.game_screen()
                if not show_menu_again:
                    self.running = False
            else:
                self.running = False
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()