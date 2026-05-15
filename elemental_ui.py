import pygame
import random
import math
from elemental_logic import *

# Layout Config
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
SIDEBAR_WIDTH = 340 
PLAY_AREA_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH
FPS = 60

# Colors
BG_COLOR = (210, 235, 245) 
BOARD_LINE_COLOR = (150, 180, 200)
SIDEBAR_COLOR = (25, 30, 35) 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 215, 0)

ELEMENT_COLORS = {
    'Pyro': (220, 60, 40),
    'Hydro': (40, 120, 220),
    'Cryo': (140, 200, 230),
    'Electro': (160, 60, 220),
}

# EFFECTS CLASSES
class Particle:
    def __init__(self, x, y, color, speed, size):
        self.x, self.y = x, y
        self.color = color
        self.size = size
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed * random.uniform(0.5, 1.5)
        self.vy = math.sin(angle) * speed * random.uniform(0.5, 1.5)
        self.lifetime = random.randint(20, 40)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.size *= 0.92  
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0 and self.size > 0.5:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))

class FloatingText:
    def __init__(self, x, y, text, color, font):
        self.x, self.y = x, y
        self.text, self.color, self.font = text, color, font
        self.lifetime = 60
        self.vy = -1.5 

    def update(self):
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime > 0:
            surf = self.font.render(self.text, True, self.color)
            shadow = self.font.render(self.text, True, BLACK)
            rect = surf.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(shadow, (rect.x + 2, rect.y + 2))
            surface.blit(surf, rect)

class ModernGameUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Elemental Alchemist: Duel of Elements")
        self.clock = pygame.time.Clock()
        
        # FONTS
        self.font_xl = pygame.font.SysFont('arial', 64, bold=True)
        self.font_l = pygame.font.SysFont('arial', 36, bold=True)
        self.font_m = pygame.font.SysFont('arial', 22, bold=True)
        self.font_s = pygame.font.SysFont('arial', 16)
        self.font_s_bold = pygame.font.SysFont('arial', 16, bold=True)

        ReactionMatrix.initialize()
        self.game = GameState()
        self.game.start_draft_phase()
        
        self.selected_cards = []
        self.card_rects = [] 
        self.particles = []
        self.floating_texts = []
        self.confirm_btn_rect = None 

        # --- LOAD BATTLEFIELD BACKGROUND ---
        try:
            raw_bg = pygame.image.load("battlefield.jpg").convert()
            self.bg_image = pygame.transform.scale(raw_bg, (PLAY_AREA_WIDTH, WINDOW_HEIGHT))
        except FileNotFoundError:
            print("Warning: battlefield.jpg not found! Using flat color instead.")
            self.bg_image = None

        # --- NEW: LOAD CARD ARTWORK ---
        self.card_images = {}
        for element in ['Pyro', 'Hydro', 'Cryo', 'Electro']:
            try:
                # Looks for pyro.png, hydro.png, etc.
                img = pygame.image.load(f"{element.lower()}.png").convert_alpha()
                self.card_images[element] = img
            except FileNotFoundError:
                print(f"Warning: {element.lower()}.png not found! Using flat color.")
                self.card_images[element] = None

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update_effects()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()

    def spawn_reaction_effect(self, reaction, multiplier):
        center_x = PLAY_AREA_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        colors = [WHITE]
        text_str = f"{reaction.name}! (x{multiplier})"
        
        if reaction == ReactionType.MELT: colors = [(255, 100, 0), (200, 230, 255), (255, 50, 50)] 
        elif reaction == ReactionType.VAPORIZE: colors = [(100, 200, 255), (255, 255, 255), (50, 100, 255)] 
        elif reaction == ReactionType.FREEZE: colors = [(200, 240, 255), (255, 255, 255)] 
        elif reaction == ReactionType.OVERLOAD: colors = [(255, 50, 50), (200, 50, 255), GOLD] 
        elif reaction == ReactionType.SUPERCONDUCT: colors = [(200, 240, 255), (200, 50, 255), WHITE] 
        elif reaction == ReactionType.SAME_ELEMENT:
            colors = [(150, 150, 150), WHITE]
            text_str = "BASIC ATTACK"

        for _ in range(50):
            self.particles.append(Particle(center_x, center_y, random.choice(colors), random.uniform(3, 10), random.uniform(4, 12)))
        self.floating_texts.append(FloatingText(center_x, center_y - 20, text_str, GOLD, self.font_xl))

    def update_effects(self):
        for p in self.particles[:]:
            p.update()
            if p.lifetime <= 0: self.particles.remove(p)
        for t in self.floating_texts[:]:
            t.update()
            if t.lifetime <= 0: self.floating_texts.remove(t)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game.phase == GamePhase.GAME_OVER:
                    self.game = GameState()
                    self.game.start_draft_phase()
                    self.selected_cards.clear()
                    self.particles.clear()
                    self.floating_texts.clear()
                    return True

                if self.game.phase == GamePhase.CAST and len(self.selected_cards) == 2:
                    if self.confirm_btn_rect and self.confirm_btn_rect.collidepoint(mouse_pos):
                        c1, c2 = self.selected_cards[0], self.selected_cards[1]
                        reaction, mult, _ = ReactionMatrix.get_reaction(c1.element, c2.element)
                        self.spawn_reaction_effect(reaction, mult)
                        self.game.execute_combat(c1, c2, True)
                        self.selected_cards.clear()
                        
                        if len(self.game.player_hand) == 2 and self.game.phase != GamePhase.GAME_OVER:
                            self.game.combat_log.append("*** AUTO-COMBINING LAST 2 CARDS! ***")
                            last_1, last_2 = self.game.player_hand[0], self.game.player_hand[1]
                            auto_reaction, auto_mult, _ = ReactionMatrix.get_reaction(last_1.element, last_2.element)
                            self.spawn_reaction_effect(auto_reaction, auto_mult)
                            self.game.execute_combat(last_1, last_2, True)

                        if len(self.game.player_hand) == 0 and self.game.phase != GamePhase.GAME_OVER:
                            self.game.turn_count += 1
                            self.game.start_draft_phase()
                        return True 

                for rect, card, origin in reversed(self.card_rects): 
                    if rect.collidepoint(mouse_pos):
                        if origin == "draft" and self.game.phase == GamePhase.DRAFT:
                            self.game.player_pick_card(card)
                            break
                        elif origin == "hand" and self.game.phase == GamePhase.CAST:
                            if card in self.selected_cards:
                                self.selected_cards.remove(card) 
                            else:
                                self.selected_cards.append(card) 
                                if len(self.selected_cards) > 2:
                                    self.selected_cards.pop(0) 
                            break
        return True

    def render(self):
        self.screen.fill(BG_COLOR) 
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            
        self.card_rects.clear()
        mouse_pos = pygame.mouse.get_pos()

        self.draw_sidebar()
        
        s = pygame.Surface((PLAY_AREA_WIDTH, 10))
        s.set_alpha(128)
        s.fill(BOARD_LINE_COLOR)
        self.screen.blit(s, (0, WINDOW_HEIGHT//2 - 5))

        self.draw_player_profile(20, 20, "You (Alchemist)", self.game.player_status)
        self.draw_player_profile(PLAY_AREA_WIDTH - 270, 20, "AI Challenger", self.game.ai_status)

        ai_card_w, ai_card_h = 90, 130 
        ai_overlap = 55 
        total_ai_w = ai_card_w + ((len(self.game.ai_hand) - 1) * ai_overlap) if self.game.ai_hand else 0
        ai_start_x = (PLAY_AREA_WIDTH - total_ai_w) // 2
        
        for i, card in enumerate(self.game.ai_hand):
            self.draw_card_back(ai_start_x + (i * ai_overlap), -30, ai_card_w, ai_card_h)

        if self.game.phase == GamePhase.DRAFT:
            self.draw_text_centered("DRAFT PHASE: Pick a card from the center", 140, WHITE, add_shadow=True)
            self.draw_draft_pool(mouse_pos)
        elif self.game.phase == GamePhase.CAST:
            self.draw_text_centered("CAST PHASE: Select 2 cards to combine!", 240, WHITE, add_shadow=True)
        elif self.game.phase == GamePhase.GAME_OVER:
            self.draw_text_centered(f"{self.game.game_winner} WINS! (Click to restart)", WINDOW_HEIGHT//2, WHITE, add_shadow=True)

        self.draw_player_hand(mouse_pos)
        
        if self.game.phase == GamePhase.CAST:
            self.draw_confirm_button(mouse_pos)

        for p in self.particles: p.draw(self.screen)
        for t in self.floating_texts: t.draw(self.screen)

        pygame.display.flip()

    def draw_player_profile(self, x, y, name, status):
        box_w, box_h = 250, 75
        
        s = pygame.Surface((box_w, box_h))
        s.set_alpha(230)
        s.fill((40, 50, 60))
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, (20, 25, 30), (x, y, box_w, box_h), 2, border_radius=8)
        
        name_surf = self.font_m.render(name, True, WHITE)
        self.screen.blit(name_surf, (x + 15, y + 10))
        
        hp_text = f"HP: {int(status.hp)} / {status.max_hp}"
        hp_color = (100, 255, 100) if status.hp > 50 else (255, 100, 100)
        hp_surf = self.font_m.render(hp_text, True, hp_color)
        self.screen.blit(hp_surf, (x + 15, y + 40))

        if status.status_effect != StatusEffect.NONE:
            stat_surf = self.font_s_bold.render(status.status_effect.name, True, (255, 150, 0))
            self.screen.blit(stat_surf, (x + 150, y + 45))

    def draw_sidebar(self):
        panel_x = PLAY_AREA_WIDTH
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (panel_x, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(self.screen, (60, 65, 70), (panel_x, 0), (panel_x, WINDOW_HEIGHT), 2)
        
        title = self.font_l.render("Battle History", True, GOLD)
        self.screen.blit(title, (panel_x + 20, 20))
        pygame.draw.line(self.screen, (60, 65, 70), (panel_x + 20, 60), (panel_x + SIDEBAR_WIDTH - 20, 60), 1)
        
        recent_logs = self.game.combat_log[-20:] 
        y_offset = 75
        for log in recent_logs:
            self.draw_rich_log_line(panel_x + 15, y_offset, log)
            y_offset += 28 

    def draw_rich_log_line(self, x, y, text):
        if "ROUND" in text or "***" in text:
            surf = self.font_s_bold.render(text, True, (255, 230, 100)) 
            self.screen.blit(surf, (x, y))
            return

        if " cast " in text and ":" in text:
            actor_part, rest = text.split(" cast ", 1)
            action_part, reaction_part = rest.split(":", 1)
            current_x = x

            actor_color = (80, 255, 100) if "Player" in actor_part else (255, 80, 80)
            surf_actor = self.font_s_bold.render(actor_part, True, actor_color)
            self.screen.blit(surf_actor, (current_x, y))
            current_x += surf_actor.get_width()

            surf_action = self.font_s.render(" cast " + action_part + ": ", True, (200, 200, 200))
            self.screen.blit(surf_action, (current_x, y))
            current_x += surf_action.get_width()

            surf_reaction = self.font_s_bold.render(reaction_part.strip(), True, GOLD)
            self.screen.blit(surf_reaction, (current_x, y))
        else:
            surf = self.font_s.render(text, True, (220, 220, 220))
            self.screen.blit(surf, (x, y))

    def draw_confirm_button(self, mouse_pos):
        if len(self.selected_cards) < 2:
            self.confirm_btn_rect = None
            return

        btn_w, btn_h = 200, 45
        btn_x = (PLAY_AREA_WIDTH - btn_w) // 2
        btn_y = WINDOW_HEIGHT - 65 

        self.confirm_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        color = (255, 230, 50) if self.confirm_btn_rect.collidepoint(mouse_pos) else (200, 170, 0)

        pygame.draw.rect(self.screen, color, self.confirm_btn_rect, border_radius=20)
        pygame.draw.rect(self.screen, BLACK, self.confirm_btn_rect, 2, border_radius=20)
        
        text = self.font_m.render("CONFIRM ATTACK", True, BLACK)
        text_rect = text.get_rect(center=self.confirm_btn_rect.center)
        self.screen.blit(text, text_rect)

    def draw_draft_pool(self, mouse_pos):
        card_w, card_h = 90, 130
        spacing = 15
        total_w = (6 * card_w) + (5 * spacing) 
        start_x = (PLAY_AREA_WIDTH - total_w) // 2
        start_y = 190 
        
        for i, card in enumerate(self.game.draft_pool):
            row = i // 6
            col = i % 6
            x = start_x + (col * (card_w + spacing))
            y = start_y + (row * (card_h + spacing))
            
            rect = pygame.Rect(x, y, card_w, card_h)
            if rect.collidepoint(mouse_pos): y -= 10 

            self.draw_front_card(x, y, card_w, card_h, card)
            self.card_rects.append((pygame.Rect(x, y, card_w, card_h), card, "draft"))

    def draw_player_hand(self, mouse_pos):
        if not self.game.player_hand: return
        card_w, card_h = 130, 190
        overlap = 60 
        total_w = card_w + ((len(self.game.player_hand)-1) * overlap)
        start_x = (PLAY_AREA_WIDTH - total_w) // 2
        base_y = WINDOW_HEIGHT - 260 

        for i, card in enumerate(self.game.player_hand):
            x = start_x + (i * overlap)
            y = base_y
            
            rect = pygame.Rect(x, y, card_w, card_h)
            is_selected = card in self.selected_cards
            
            if is_selected: y -= 30
            elif rect.collidepoint(mouse_pos): y -= 15

            self.draw_front_card(x, y, card_w, card_h, card, is_selected)
            self.card_rects.append((pygame.Rect(x, y, card_w, card_h), card, "hand"))

    def draw_front_card(self, x, y, w, h, card, selected=False):
        # --- NEW: DRAW ARTWORK IF IT EXISTS ---
        img = self.card_images.get(card.element)
        if img:
            # Scale the image to fit the current card size (hand vs draft pool)
            scaled_img = pygame.transform.scale(img, (w, h))
            self.screen.blit(scaled_img, (x, y))
            # Draw a clean black border around the artwork
            pygame.draw.rect(self.screen, BLACK, (x, y, w, h), 2, border_radius=8)
        else:
            # Fallback to the colored rectangles if image is missing
            color = ELEMENT_COLORS.get(card.element, WHITE)
            pygame.draw.rect(self.screen, color, (x, y, w, h), border_radius=10)
            pygame.draw.rect(self.screen, BLACK, (x+5, y+5, w-10, h-10), 2, border_radius=8)
            
            text = self.font_m.render(card.element, True, WHITE)
            shadow = self.font_m.render(card.element, True, BLACK)
            text_rect = text.get_rect(center=(x + w//2, y + h//2))
            self.screen.blit(shadow, (text_rect.x+2, text_rect.y+2))
            self.screen.blit(text, text_rect)

        # Draw the Golden Selection Highlight over the top!
        if selected:
            pygame.draw.rect(self.screen, GOLD, (x-2, y-2, w+4, h+4), 4, border_radius=12)

    def draw_card_back(self, x, y, w, h):
        pygame.draw.rect(self.screen, (80, 50, 50), (x, y, w, h), border_radius=10)
        pygame.draw.rect(self.screen, GOLD, (x+5, y+5, w-10, h-10), 2, border_radius=8)
        pygame.draw.circle(self.screen, GOLD, (x + w//2, y + h//2), 20, 3)

    def draw_text_centered(self, text, y, color, add_shadow=False):
        surf = self.font_l.render(text, True, color)
        rect = surf.get_rect(center=(PLAY_AREA_WIDTH//2, y))
        
        if add_shadow:
            shadow = self.font_l.render(text, True, BLACK)
            self.screen.blit(shadow, (rect.x + 2, rect.y + 2))
            
        self.screen.blit(surf, rect)

if __name__ == "__main__":
    ui = ModernGameUI()
    ui.run()