from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QKeyEvent, QFont
from PyQt6.QtCore import QBasicTimer, Qt, QRect, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import sys
import random
import os

# Constants
BOARD_WIDTH = 10
BOARD_HEIGHT = 25
TILE_SIZE = 30

SHAPES = {
    'NoShape': [],
    'ZShape': [[1, 1, 0],
               [0, 1, 1]],
    'SShape': [[0, 1, 1],
               [1, 1, 0]],
    'LineShape': [[1, 1, 1, 1]],
    'TShape': [[0, 1, 0],
               [1, 1, 1]],
    'SquareShape': [[1, 1],
                    [1, 1]],
    'LShape': [[1, 0],
               [1, 0],
               [1, 1]],
    'MirroredLShape': [[0, 1],
                       [0, 1],
                       [1, 1]],
}

class Tetromino:
    def __init__(self, shape_name):
        self.shape = SHAPES[shape_name]
        self.shape_name = shape_name

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class TetrisBoard(QWidget):
    score_changed = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(BOARD_WIDTH * TILE_SIZE, BOARD_HEIGHT * TILE_SIZE)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.timer = QBasicTimer()
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.score = 0
        self.is_game_over = False

        # Game over label
        self.game_over_label = QLabel("GAME OVER", self)
        self.game_over_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.game_over_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.game_over_label.setStyleSheet("color: white; background-color: black;")
        self.game_over_label.setGeometry(0, BOARD_HEIGHT * TILE_SIZE // 2 - 50, BOARD_WIDTH * TILE_SIZE, 100)
        self.game_over_label.hide()

        # Single reusable media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # Sound files
        self.sounds = {
            "clear": os.path.join("music", "tetrisclear.mp3"),
            "game_over": os.path.join("music", "DUN.mp3")
        }

        self.init_game()

    def init_game(self):
        self.new_piece()
        self.timer.start(300, self)

    def new_piece(self):
        shape = random.choice(list(SHAPES.keys())[1:])
        self.current_piece = Tetromino(shape)
        self.current_x = BOARD_WIDTH // 2 - 1
        self.current_y = 0
        if not self.is_valid_position():
            self.end_game()

    def end_game(self):
        self.timer.stop()
        self.is_game_over = True
        self.game_over_label.show()
        self.play_sound("game_over")
        self.update()

    def is_valid_position(self, dx=0, dy=0):
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_x + x + dx
                    new_y = self.current_y + y + dy
                    if (new_x < 0 or new_x >= BOARD_WIDTH or
                        new_y >= BOARD_HEIGHT or
                        (new_y >= 0 and self.board[new_y][new_x] > 0)):
                        return False
        return True

    def lock_piece(self):
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.board[self.current_y + y][self.current_x + x] = 1
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        cleared_lines = BOARD_HEIGHT - len(new_board)
        if cleared_lines > 0:
            self.score += cleared_lines ** 2
            self.score_changed.emit(self.score)
            self.board = [[0] * BOARD_WIDTH for _ in range(cleared_lines)] + new_board
            self.play_sound("clear")
        self.update()

    def play_sound(self, sound_key):
        sound_path = self.sounds.get(sound_key)
        if sound_path and os.path.exists(sound_path):
            self.media_player.stop()
            self.media_player.setSource(QUrl.fromLocalFile(sound_path))
            self.media_player.play()

    def paintEvent(self, event):
        painter = QPainter(self)
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                if self.board[y][x]:
                    self.draw_tile(painter, x, y, QColor(50, 150, 200))

        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_tile(painter, self.current_x + x, self.current_y + y, QColor(200, 50, 50))

    def draw_tile(self, painter, x, y, color):
        painter.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, color)
        painter.drawRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def keyPressEvent(self, event: QKeyEvent):
        if not self.current_piece or self.is_game_over:
            return
        if event.key() == Qt.Key.Key_Left and self.is_valid_position(-1, 0):
            self.current_x -= 1
        elif event.key() == Qt.Key.Key_Right and self.is_valid_position(1, 0):
            self.current_x += 1
        elif event.key() == Qt.Key.Key_Down and self.is_valid_position(0, 1):
            self.current_y += 1
        elif event.key() == Qt.Key.Key_Up:
            self.current_piece.rotate()
            if not self.is_valid_position():
                self.current_piece.rotate()
        elif event.key() == Qt.Key.Key_Space:
            while self.is_valid_position(0, 1):
                self.current_y += 1
            self.lock_piece()
        self.update()

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.is_valid_position(0, 1):
                self.current_y += 1
            else:
                self.lock_piece()
            self.update()

class Tetris(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tetris")
        self.tetris_board = TetrisBoard(self)
        self.score_label = QLabel("Score: 0", self)
        self.tetris_board.score_changed.connect(self.update_score)

        layout = QVBoxLayout()
        layout.addWidget(self.score_label)
        layout.addWidget(self.tetris_board)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setFixedSize(BOARD_WIDTH * TILE_SIZE + 20, BOARD_HEIGHT * TILE_SIZE + 60)

        # Background music setup
        self.background_music_player = QMediaPlayer()
        self.background_audio_output = QAudioOutput()
        self.background_music_player.setAudioOutput(self.background_audio_output)

        music_path = os.path.join("music", "gangmanstyle.mp3")
        if os.path.exists(music_path):
            self.background_music_player.setSource(QUrl.fromLocalFile(music_path))
            self.background_music_player.setLoops(QMediaPlayer.Loops.Infinite)
            self.background_music_player.play()

    def update_score(self, score):
        self.score_label.setText(f"Score: {score}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Tetris()
    window.show()
    sys.exit(app.exec())