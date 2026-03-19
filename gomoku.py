from __future__ import annotations

import os
import random
import sys

import pygame


def resource_path(relative_path: str) -> str:
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class GameLogic:
    BOARD_SIZE = 15

    def __init__(self) -> None:
        self.board = [[0 for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        self.current_player = 1
        self.game_over = False
        self.winner = 0

    def is_valid_move(self, row: int, col: int) -> bool:
        if not (0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE):
            return False
        return self.board[row][col] == 0 and not self.game_over

    def make_move(self, row: int, col: int) -> bool:
        if not self.is_valid_move(row, col):
            return False

        self.board[row][col] = self.current_player

        if self.check_win(row, col, self.current_player):
            self.game_over = True
            self.winner = self.current_player
        elif self.check_draw():
            self.game_over = True
            self.winner = 0
        else:
            self.current_player = 3 - self.current_player

        return True

    def check_win(self, start_row: int, start_col: int, player: int) -> bool:
        directions = [
            [(0, 1), (0, -1)],
            [(1, 0), (-1, 0)],
            [(1, 1), (-1, -1)],
            [(1, -1), (-1, 1)],
        ]

        for direction_pair in directions:
            count = 1

            for dx, dy in direction_pair:
                temp_row, temp_col = start_row, start_col

                while True:
                    temp_row += dx
                    temp_col += dy

                    if (0 <= temp_row < self.BOARD_SIZE and
                            0 <= temp_col < self.BOARD_SIZE and
                            self.board[temp_row][temp_col] == player):
                        count += 1
                    else:
                        break

            if count >= 5:
                return True

        return False

    def check_draw(self) -> bool:
        for row in self.board:
            if 0 in row:
                return False
        return True

    def reset(self) -> None:
        self.board = [[0 for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        self.current_player = 1
        self.game_over = False
        self.winner = 0


class GameRenderer:
    GRID_SIZE = 40
    MARGIN = 60
    PIECE_RADIUS = 16
    LINE_WIDTH = 1
    BOARD_BORDER_PADDING = 10
    STAR_POINTS = ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11))
    STAR_POINT_RADIUS = 4
    MUSIC_RIGHT_MARGIN = 20
    TEXT_TO_BOARD_GAP = 8

    PAPER_WHITE = (248, 246, 240)
    INK_BLACK = (45, 45, 45)
    DARK_WOOD = (168, 124, 90)
    LIGHT_WOOD = (210, 180, 140)
    ACCENT_RED = (180, 70, 60)
    ACCENT_BLUE = (80, 110, 140)
    MUSIC_DISABLED = (150, 150, 150)
    STONE_BLACK = (60, 60, 60)
    STONE_WHITE = (230, 225, 210)
    STONE_BLACK_HIGHLIGHT = (100, 100, 100)
    STONE_WHITE_HIGHLIGHT = (200, 200, 190)
    ICON_ASSET_PATH = os.path.join("assets", "AppIcon.png")
    FONT_ASSET_PATH = os.path.join("assets", "fonts", "OtsutomeFont_Ver3_20.ttf")
    TITLE_TEXT = "五目並べ"
    UI_FONT_SIZE = 22
    STATUS_TEXTS = {
        "black_turn": "現在: 黒の番",
        "white_turn": "現在: 白の番",
        "black_win": "黒の勝ち！ Rキーで再開",
        "white_win": "白の勝ち！ Rキーで再開",
        "draw": "引き分け！ Rキーで再開",
    }
    MUSIC_TEXTS = {
        "playing": "音楽: ON",
        "paused": "音楽: OFF",
        "disabled": "音楽: OFF",
    }

    def __init__(self, board_size: int) -> None:
        self.board_size = board_size
        self.window_size = 2 * self.MARGIN + (self.board_size - 1) * self.GRID_SIZE

        pygame.init()
        pygame.display.set_caption("Gomoku")
        icon_surface = pygame.image.load(resource_path(self.ICON_ASSET_PATH))
        pygame.display.set_icon(icon_surface)
        self.screen = pygame.display.set_mode((self.window_size, self.window_size))

        self.ui_font = self.load_font(self.UI_FONT_SIZE)
        self.title_surface = self.render_text_surface(
            self.TITLE_TEXT,
            self.INK_BLACK,
        )
        self.status_surfaces = self.build_status_surfaces()
        self.music_surfaces = self.build_music_surfaces()
        self.music_button_rect = self.build_music_button_rect()

    def load_font(self, font_size: int) -> pygame.font.Font:
        font_path = resource_path(self.FONT_ASSET_PATH)
        if not os.path.isfile(font_path):
            raise FileNotFoundError(
                f"找不到字体文件: {font_path}. 请确认 OtsutomeFont_Ver3_20.ttf 已放入 assets/fonts."
            )

        try:
            return pygame.font.Font(font_path, font_size)
        except (FileNotFoundError, pygame.error) as error:
            raise RuntimeError(f"加载字体失败: {font_path}") from error

    def render_text_surface(
        self,
        text: str,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        return self.ui_font.render(text, True, color).convert_alpha()

    def build_status_surfaces(self) -> dict[str, pygame.Surface]:
        return {
            "black_turn": self.render_text_surface(
                self.STATUS_TEXTS["black_turn"],
                self.ACCENT_BLUE,
            ),
            "white_turn": self.render_text_surface(
                self.STATUS_TEXTS["white_turn"],
                self.ACCENT_BLUE,
            ),
            "black_win": self.render_text_surface(
                self.STATUS_TEXTS["black_win"],
                self.ACCENT_RED,
            ),
            "white_win": self.render_text_surface(
                self.STATUS_TEXTS["white_win"],
                self.ACCENT_RED,
            ),
            "draw": self.render_text_surface(
                self.STATUS_TEXTS["draw"],
                self.ACCENT_RED,
            ),
        }

    def build_music_surfaces(self) -> dict[str, pygame.Surface]:
        return {
            "playing": self.render_text_surface(
                self.MUSIC_TEXTS["playing"],
                self.ACCENT_BLUE,
            ),
            "paused": self.render_text_surface(
                self.MUSIC_TEXTS["paused"],
                self.ACCENT_BLUE,
            ),
            "disabled": self.render_text_surface(
                self.MUSIC_TEXTS["disabled"],
                self.MUSIC_DISABLED,
            ),
        }

    def get_board_rect(self) -> pygame.Rect:
        padding = self.BOARD_BORDER_PADDING
        return pygame.Rect(
            self.MARGIN - padding,
            self.MARGIN - padding,
            self.window_size - 2 * self.MARGIN + 2 * padding,
            self.window_size - 2 * self.MARGIN + 2 * padding,
        )

    def build_music_button_rect(self) -> pygame.Rect:
        board_rect = self.get_board_rect()
        button_width = max(surface.get_width() for surface in self.music_surfaces.values())
        button_height = max(surface.get_height() for surface in self.music_surfaces.values())
        button_x = self.window_size - button_width - self.MUSIC_RIGHT_MARGIN
        button_y = board_rect.top - self.TEXT_TO_BOARD_GAP - button_height
        return pygame.Rect(button_x, button_y, button_width, button_height)

    def grid_to_screen(self, row: int, col: int) -> tuple[int, int]:
        return self.MARGIN + col * self.GRID_SIZE, self.MARGIN + row * self.GRID_SIZE

    def draw_board(self) -> None:
        self.screen.fill(self.PAPER_WHITE)

        board_rect = self.get_board_rect()
        pygame.draw.rect(
            self.screen,
            self.LIGHT_WOOD,
            board_rect,
        )

        for i in range(self.board_size):
            pygame.draw.line(
                self.screen,
                self.DARK_WOOD,
                (self.MARGIN, self.MARGIN + i * self.GRID_SIZE),
                (self.window_size - self.MARGIN, self.MARGIN + i * self.GRID_SIZE),
                self.LINE_WIDTH,
            )
            pygame.draw.line(
                self.screen,
                self.DARK_WOOD,
                (self.MARGIN + i * self.GRID_SIZE, self.MARGIN),
                (self.MARGIN + i * self.GRID_SIZE, self.window_size - self.MARGIN),
                self.LINE_WIDTH,
            )

        for row, col in self.STAR_POINTS:
            pygame.draw.circle(
                self.screen,
                self.INK_BLACK,
                self.grid_to_screen(row, col),
                self.STAR_POINT_RADIUS,
            )

    def draw_black_piece(self, center: tuple[int, int]) -> None:
        center_x, center_y = center
        pygame.draw.circle(
            self.screen,
            self.STONE_BLACK,
            center,
            self.PIECE_RADIUS,
        )
        pygame.draw.circle(
            self.screen,
            self.STONE_BLACK_HIGHLIGHT,
            (
                center_x - self.PIECE_RADIUS // 3,
                center_y - self.PIECE_RADIUS // 3,
            ),
            self.PIECE_RADIUS // 4,
        )

    def draw_white_piece(self, center: tuple[int, int]) -> None:
        center_x, center_y = center
        pygame.draw.circle(
            self.screen,
            self.STONE_WHITE,
            center,
            self.PIECE_RADIUS,
        )
        pygame.draw.circle(
            self.screen,
            self.DARK_WOOD,
            center,
            self.PIECE_RADIUS,
            1,
        )
        pygame.draw.circle(
            self.screen,
            self.STONE_WHITE_HIGHLIGHT,
            (
                center_x + self.PIECE_RADIUS // 4,
                center_y + self.PIECE_RADIUS // 4,
            ),
            self.PIECE_RADIUS // 3,
        )

    def draw_pieces(self, board: list[list[int]]) -> None:
        for i in range(self.board_size):
            for j in range(self.board_size):
                center = self.grid_to_screen(i, j)
                if board[i][j] == 1:
                    self.draw_black_piece(center)
                elif board[i][j] == 2:
                    self.draw_white_piece(center)

    @staticmethod
    def get_status_key(current_player: int, game_over: bool, winner: int) -> str:
        if game_over:
            if winner == 1:
                return "black_win"
            if winner == 2:
                return "white_win"
            return "draw"

        if current_player == 1:
            return "black_turn"
        return "white_turn"

    def draw_game_status(
        self,
        status_key: str,
        music_toggle_enabled: bool,
        music_playing: bool,
    ) -> None:
        board_rect = self.get_board_rect()
        title_y = board_rect.top - self.TEXT_TO_BOARD_GAP - self.title_surface.get_height()
        self.screen.blit(
            self.title_surface,
            (self.window_size // 2 - self.title_surface.get_width() // 2, title_y),
        )

        status_surface = self.get_status_surface(status_key)
        status_y = board_rect.bottom + self.TEXT_TO_BOARD_GAP
        self.screen.blit(
            status_surface,
            (
                self.window_size // 2 - status_surface.get_width() // 2,
                status_y,
            ),
        )

        music_surface, music_rect = self.get_music_surface_and_rect(
            music_toggle_enabled,
            music_playing,
        )
        self.screen.blit(music_surface, music_rect.topleft)

    def is_music_button_clicked(
        self,
        mouse_x: int,
        mouse_y: int,
        music_toggle_enabled: bool,
    ) -> bool:
        if not music_toggle_enabled:
            return False
        return self.music_button_rect.collidepoint(mouse_x, mouse_y)

    def get_status_surface(self, status_key: str) -> pygame.Surface:
        return self.status_surfaces[status_key]

    def get_music_surface_and_rect(
        self,
        music_toggle_enabled: bool,
        music_playing: bool,
    ) -> tuple[pygame.Surface, pygame.Rect]:
        if music_toggle_enabled and music_playing:
            music_surface = self.music_surfaces["playing"]
        elif music_toggle_enabled:
            music_surface = self.music_surfaces["paused"]
        else:
            music_surface = self.music_surfaces["disabled"]

        music_rect = music_surface.get_rect(topleft=self.music_button_rect.topleft)
        return music_surface, music_rect

    def screen_to_grid(self, mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
        col = round((mouse_x - self.MARGIN) / self.GRID_SIZE)
        row = round((mouse_y - self.MARGIN) / self.GRID_SIZE)

        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return None

        grid_x, grid_y = self.grid_to_screen(row, col)
        dx = mouse_x - grid_x
        dy = mouse_y - grid_y
        if dx * dx + dy * dy > self.PIECE_RADIUS * self.PIECE_RADIUS:
            return None

        return row, col

    @staticmethod
    def update_display() -> None:
        pygame.display.flip()


class MusicController:
    SUPPORTED_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mid")
    MUSIC_DIR = os.path.join("assets", "music")
    LOAD_STATE_READY = "ready"
    LOAD_STATE_NO_FILES = "no_files"
    LOAD_STATE_AUDIO_ERROR = "audio_error"
    LOAD_STATE_LOAD_ERROR = "load_error"

    def __init__(self) -> None:
        self.music_playing = False
        self.load_state = None

    def can_toggle_music(self) -> bool:
        return self.load_state == self.LOAD_STATE_READY

    def initialize_audio(self) -> bool:
        if pygame.mixer.get_init() is not None:
            return True

        try:
            pygame.mixer.init()
            return True
        except pygame.error as error:
            print(f"音声デバイス初期化エラー: {error}")
            self.load_state = self.LOAD_STATE_AUDIO_ERROR
            self.music_playing = False
            return False

    def find_music_files(self) -> list[str]:
        try:
            base_path = resource_path(self.MUSIC_DIR)

            if not os.path.isdir(base_path):
                return []

            music_files = []
            for root, _, files in os.walk(base_path):
                for file in files:
                    file_lower = file.lower()
                    if any(file_lower.endswith(ext) for ext in self.SUPPORTED_EXTENSIONS):
                        music_files.append(os.path.join(root, file))

            return sorted(music_files)
        except Exception as e:
            print(f"音楽ファイル検索エラー: {e}")
            return []

    def load_music(self) -> None:
        if not self.initialize_audio():
            return

        try:
            music_files = self.find_music_files()

            if not music_files:
                self.load_state = self.LOAD_STATE_NO_FILES
                self.music_playing = False
                return

            selected_music = random.choice(music_files)
            pygame.mixer.music.load(selected_music)
            pygame.mixer.music.play(-1)
            self.music_playing = True
            self.load_state = self.LOAD_STATE_READY

        except Exception as e:
            print(f"音楽ファイル読み込みエラー: {e}")
            self.load_state = self.LOAD_STATE_LOAD_ERROR
            self.music_playing = False

    def toggle_music(self) -> None:
        if not self.can_toggle_music():
            return

        if self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False
        else:
            pygame.mixer.music.unpause()
            self.music_playing = True


class GomokuGame:
    FRAME_RATE = 60

    def __init__(self) -> None:
        self.game_logic = GameLogic()
        self.renderer = GameRenderer(self.game_logic.BOARD_SIZE)
        self.music_controller = MusicController()
        self.clock = pygame.time.Clock()

    def handle_mouse_click(self, mouse_x: int, mouse_y: int) -> None:
        music_toggle_enabled = self.music_controller.can_toggle_music()
        if self.renderer.is_music_button_clicked(
            mouse_x,
            mouse_y,
            music_toggle_enabled,
        ):
            self.music_controller.toggle_music()
        elif not self.game_logic.game_over:
            grid_position = self.renderer.screen_to_grid(mouse_x, mouse_y)
            if grid_position is None:
                return

            row, col = grid_position
            self.game_logic.make_move(row, col)

    def reset_game(self) -> None:
        self.game_logic.reset()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.reset_game()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            self.handle_mouse_click(mouse_x, mouse_y)

    def render_frame(self) -> None:
        status_key = self.renderer.get_status_key(
            self.game_logic.current_player,
            self.game_logic.game_over,
            self.game_logic.winner,
        )
        music_toggle_enabled = self.music_controller.can_toggle_music()
        self.renderer.draw_board()
        self.renderer.draw_pieces(self.game_logic.board)
        self.renderer.draw_game_status(
            status_key,
            music_toggle_enabled,
            self.music_controller.music_playing,
        )
        self.renderer.update_display()

    def run(self) -> None:
        pygame.key.stop_text_input()
        self.music_controller.load_music()

        while True:
            for event in pygame.event.get():
                self.handle_event(event)

            self.render_frame()
            self.clock.tick(self.FRAME_RATE)


def main() -> None:
    game = GomokuGame()
    game.run()


if __name__ == "__main__":
    main()
