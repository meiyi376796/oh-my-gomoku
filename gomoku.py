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
    DIRECTIONS = (
        ((0, 1), (0, -1)),
        ((1, 0), (-1, 0)),
        ((1, 1), (-1, -1)),
        ((1, -1), (-1, 1)),
    )

    def __init__(self) -> None:
        self.reset()

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
        for direction_pair in self.DIRECTIONS:
            count = 1

            for d_row, d_col in direction_pair:
                temp_row, temp_col = start_row, start_col

                while True:
                    temp_row += d_row
                    temp_col += d_col

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
    MARGIN = 82
    PIECE_RADIUS = 16
    LINE_WIDTH = 1
    BOARD_BORDER_PADDING = 10
    STAR_POINTS = ((3, 3), (3, 11), (7, 7), (11, 3), (11, 11))
    STAR_POINT_RADIUS = 4

    PAPER_WHITE = (245, 240, 229)
    INK_BLACK = (56, 52, 47)
    DARK_WOOD = (154, 118, 82)
    LIGHT_WOOD = (213, 181, 138)
    ACCENT_RED = (186, 82, 68)
    ACCENT_BLUE = (96, 116, 134)
    MUSIC_DISABLED = (158, 152, 141)
    STONE_BLACK = (50, 47, 43)
    STONE_WHITE = (234, 227, 212)
    STONE_BLACK_HIGHLIGHT = (95, 90, 84)
    STONE_WHITE_HIGHLIGHT = (203, 196, 181)
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
    MUSIC_LABEL_TEXT = "音楽: "
    MUSIC_STATE_TEXTS = {
        "playing": "ON",
        "paused": "OFF",
        "disabled": "OFF",
    }

    def __init__(self, board_size: int) -> None:
        self.board_size = board_size
        self.window_size = 2 * self.MARGIN + (self.board_size - 1) * self.GRID_SIZE + 1

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
        self.music_label_surfaces = self.build_music_label_surfaces()
        self.music_text_center_y = self.get_board_rect().top // 2
        self.black_piece_surface, self.white_piece_surface = self.build_piece_surfaces()
        self.board_surface = self.build_board_surface()

    def load_font(self, font_size: int) -> pygame.font.Font:
        font_path = resource_path(self.FONT_ASSET_PATH)
        if not os.path.isfile(font_path):
            raise FileNotFoundError(
                f"フォントファイルが見つかりません: {font_path}. "
                "OtsutomeFont_Ver3_20.ttf を assets/fonts に配置してください."
            )

        try:
            return pygame.font.Font(font_path, font_size)
        except (FileNotFoundError, pygame.error) as error:
            raise RuntimeError(f"フォントの読み込みに失敗しました: {font_path}") from error

    def render_text_surface(
        self,
        text: str,
        color: tuple[int, int, int],
    ) -> pygame.Surface:
        return self.ui_font.render(text, True, color).convert_alpha()

    def build_status_surfaces(self) -> dict[str, pygame.Surface]:
        return {
            key: self.render_text_surface(
                text,
                self.ACCENT_BLUE if key.endswith("_turn") else self.ACCENT_RED,
            )
            for key, text in self.STATUS_TEXTS.items()
        }

    def build_music_surfaces(self) -> dict[str, pygame.Surface]:
        return {
            key: self.render_text_surface(
                text,
                self.MUSIC_DISABLED if key == "disabled" else self.ACCENT_BLUE,
            )
            for key, text in self.MUSIC_STATE_TEXTS.items()
        }

    def build_music_label_surfaces(self) -> dict[str, pygame.Surface]:
        return {
            key: self.render_text_surface(self.MUSIC_LABEL_TEXT, color)
            for key, color in (
                ("enabled", self.ACCENT_BLUE),
                ("disabled", self.MUSIC_DISABLED),
            )
        }

    def get_board_rect(self) -> pygame.Rect:
        padding = self.BOARD_BORDER_PADDING
        return pygame.Rect(
            self.MARGIN - padding,
            self.MARGIN - padding,
            self.window_size - 2 * self.MARGIN + 2 * padding,
            self.window_size - 2 * self.MARGIN + 2 * padding,
        )

    def grid_to_screen(self, row: int, col: int) -> tuple[int, int]:
        return self.MARGIN + col * self.GRID_SIZE, self.MARGIN + row * self.GRID_SIZE

    def build_board_surface(self) -> pygame.Surface:
        surface = pygame.Surface((self.window_size, self.window_size))
        surface.fill(self.PAPER_WHITE)

        pygame.draw.rect(
            surface,
            self.LIGHT_WOOD,
            self.get_board_rect(),
        )

        grid_end = self.MARGIN + (self.board_size - 1) * self.GRID_SIZE
        for i in range(self.board_size):
            pygame.draw.line(
                surface,
                self.DARK_WOOD,
                (self.MARGIN, self.MARGIN + i * self.GRID_SIZE),
                (grid_end, self.MARGIN + i * self.GRID_SIZE),
                self.LINE_WIDTH,
            )
            pygame.draw.line(
                surface,
                self.DARK_WOOD,
                (self.MARGIN + i * self.GRID_SIZE, self.MARGIN),
                (self.MARGIN + i * self.GRID_SIZE, grid_end),
                self.LINE_WIDTH,
            )

        for row, col in self.STAR_POINTS:
            star_x, star_y = self.grid_to_screen(row, col)
            self.draw_centered_disc(
                surface,
                star_x,
                star_y,
                self.STAR_POINT_RADIUS,
                self.INK_BLACK,
            )

        return surface.convert()

    def draw_board(self) -> None:
        self.screen.blit(self.board_surface, (0, 0))

    @staticmethod
    def disc_threshold(radius: int) -> int:
        return radius * radius + radius // 2

    @staticmethod
    def draw_centered_disc(
        surface: pygame.Surface,
        center_x: int,
        center_y: int,
        radius: int,
        color: tuple[int, int, int],
        width: int = 0,
    ) -> None:
        outer_threshold = GameRenderer.disc_threshold(radius)
        inner_threshold = (
            GameRenderer.disc_threshold(radius - width) if width > 0 else -1
        )
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                distance_squared = dx * dx + dy * dy
                if inner_threshold < distance_squared <= outer_threshold:
                    surface.set_at((center_x + dx, center_y + dy), color)

    def build_piece_surfaces(self) -> tuple[pygame.Surface, pygame.Surface]:
        radius = self.PIECE_RADIUS
        size = 2 * radius + 1

        black_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        self.draw_centered_disc(black_surface, radius, radius, radius, self.STONE_BLACK)
        self.draw_centered_disc(
            black_surface,
            radius - radius // 3,
            radius - radius // 3,
            radius // 4,
            self.STONE_BLACK_HIGHLIGHT,
        )

        white_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        self.draw_centered_disc(white_surface, radius, radius, radius, self.STONE_WHITE)
        self.draw_centered_disc(
            white_surface, radius, radius, radius, self.DARK_WOOD, width=1
        )
        self.draw_centered_disc(
            white_surface,
            radius + radius // 4,
            radius + radius // 4,
            radius // 3,
            self.STONE_WHITE_HIGHLIGHT,
        )

        return black_surface, white_surface

    def draw_pieces(self, board: list[list[int]]) -> None:
        for row in range(self.board_size):
            for col in range(self.board_size):
                center = self.grid_to_screen(row, col)
                top_left = (
                    center[0] - self.PIECE_RADIUS,
                    center[1] - self.PIECE_RADIUS,
                )
                if board[row][col] == 1:
                    self.screen.blit(self.black_piece_surface, top_left)
                elif board[row][col] == 2:
                    self.screen.blit(self.white_piece_surface, top_left)

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
        title_y = (board_rect.top - self.title_surface.get_height()) // 2
        self.screen.blit(
            self.title_surface,
            (self.window_size // 2 - self.title_surface.get_width() // 2, title_y),
        )

        status_surface = self.status_surfaces[status_key]
        status_y = board_rect.bottom + (
            self.window_size - board_rect.bottom - status_surface.get_height()
        ) // 2
        self.screen.blit(
            status_surface,
            (
                self.window_size // 2 - status_surface.get_width() // 2,
                status_y,
            ),
        )

        label_surface, state_surface = self.get_music_surfaces(
            music_toggle_enabled,
            music_playing,
        )
        label_rect = label_surface.get_rect(
            midright=(board_rect.right, self.music_text_center_y)
        )
        state_rect = state_surface.get_rect(
            midleft=(board_rect.right, self.music_text_center_y)
        )
        self.screen.blit(label_surface, label_rect)
        self.screen.blit(state_surface, state_rect)

    def is_music_button_clicked(
        self,
        mouse_x: int,
        mouse_y: int,
        music_toggle_enabled: bool,
        music_playing: bool,
    ) -> bool:
        if not music_toggle_enabled:
            return False
        label_surface, state_surface = self.get_music_surfaces(
            music_toggle_enabled, music_playing
        )
        hit_height = max(label_surface.get_height(), state_surface.get_height())
        hit_rect = pygame.Rect(
            self.get_board_rect().right - label_surface.get_width(),
            self.music_text_center_y - hit_height // 2,
            label_surface.get_width() + state_surface.get_width(),
            hit_height,
        )
        return hit_rect.collidepoint(mouse_x, mouse_y)

    def get_music_surfaces(
        self,
        music_toggle_enabled: bool,
        music_playing: bool,
    ) -> tuple[pygame.Surface, pygame.Surface]:
        if music_toggle_enabled and music_playing:
            state_key = "playing"
        elif music_toggle_enabled:
            state_key = "paused"
        else:
            state_key = "disabled"

        label_key = "enabled" if music_toggle_enabled else "disabled"
        return self.music_label_surfaces[label_key], self.music_surfaces[state_key]

    def screen_to_grid(self, mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
        col = round((mouse_x - self.MARGIN) / self.GRID_SIZE)
        row = round((mouse_y - self.MARGIN) / self.GRID_SIZE)

        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return None

        grid_x, grid_y = self.grid_to_screen(row, col)
        dx = mouse_x - grid_x
        dy = mouse_y - grid_y
        if dx * dx + dy * dy > self.disc_threshold(self.PIECE_RADIUS):
            return None

        return row, col


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
        except OSError as error:
            print(f"音楽ファイル検索エラー: {error}")
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

        except (pygame.error, OSError) as error:
            print(f"音楽ファイル読み込みエラー: {error}")
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
            self.music_controller.music_playing,
        ):
            self.music_controller.toggle_music()
        elif not self.game_logic.game_over:
            grid_position = self.renderer.screen_to_grid(mouse_x, mouse_y)
            if grid_position is None:
                return

            row, col = grid_position
            self.game_logic.make_move(row, col)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.game_logic.reset()

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
        pygame.display.flip()

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
