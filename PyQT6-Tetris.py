from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QKeyEvent
from PyQt6.QtCore import QBasicTimer, Qt, QRect, pyqtSignal
import sys
import random

# Constants
BOARD_WIDTH = 10  # Width of the Tetris board
BOARD_HEIGHT = 20  # Height of the Tetris board
TILE_SIZE = 30  # Size of each Tetris tile in pixels

# Define Tetromino shapes and rotations
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

# Tetromino class to represent shapes and their rotations
class Tetromino:
    def __init__(self, shape_name):
        self.shape = SHAPES[shape_name]
        self.shape_name = shape_name

    def rotate(self):
        """ Rotate the shape 90 degrees clockwise. """
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

# Tetris Board class
class TetrisBoard(QWidget):
    score_changed = pyqtSignal(int)  # Signal to notify score updates

    def __init__(self, parent):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Set focus for key events
        self.board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.timer = QBasicTimer()
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.score = 0
        self.init_game()

    def init_game(self):
        """ Initialize game state and start timer. """
        self.new_piece()
        self.timer.start(300, self)  # Controls game speed

    def new_piece(self):
        """ Generate a new random piece and reset position. """
        shape = random.choice(list(SHAPES.keys())[1:])  # Skip 'NoShape'
        self.current_piece = Tetromino(shape)
        self.current_x = BOARD_WIDTH // 2 - 1
        self.current_y = 0
        if not self.is_valid_position():
            self.timer.stop()  # Game over if no space for new piece
            self.update()

    def is_valid_position(self, dx=0, dy=0):
        """ Check if the piece can be placed at a new position (x + dx, y + dy). """
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    new_x = self.current_x + x + dx
                    new_y = self.current_y + y + dy
                    if (new_x < 0 or new_x >= BOARD_WIDTH or new_y >= BOARD_HEIGHT or
                            (new_y >= 0 and self.board[new_y][new_x] > 0)):
                        return False
        return True

    def lock_piece(self):
        """ Lock the piece into the board and check for complete lines. """
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.board[self.current_y + y][self.current_x + x] = 1
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        """ Check and remove completed lines, update score. """
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        cleared_lines = BOARD_HEIGHT - len(new_board)
        if cleared_lines > 0:
            self.score += cleared_lines ** 2  # Simple scoring
            self.score_changed.emit(self.score)  # Emit the score change signal
            self.board = [[0] * BOARD_WIDTH] * cleared_lines + new_board
        self.update()

    def paintEvent(self, event):
        """ Render the board and current piece. """
        painter = QPainter(self)
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                if self.board[y][x]:
                    self.draw_tile(painter, x, y, QColor(50, 150, 200))  # Blue color for locked pieces

        # Draw current piece in its current position
        if self.current_piece:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_tile(painter, self.current_x + x, self.current_y + y, QColor(200, 50, 50))  # Red color

    def draw_tile(self, painter, x, y, color):
        """ Draw individual tile at board position (x, y) with a given color. """
        painter.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, color)
        painter.drawRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def keyPressEvent(self, event: QKeyEvent):
        """ Handle key events for moving and rotating the piece. """
        if not self.current_piece:
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
                self.current_piece.rotate()  # Undo rotation if invalid
        elif event.key() == Qt.Key.Key_Space:
            while self.is_valid_position(0, 1):
                self.current_y += 1
            self.lock_piece()
        self.update()

    def timerEvent(self, event):
        """ Timer event to move the piece down at regular intervals. """
        if event.timerId() == self.timer.timerId():
            if self.is_valid_position(0, 1):
                self.current_y += 1
            else:
                self.lock_piece()
            self.update()

# Main application window
class Tetris(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tetris")
        self.tetris_board = TetrisBoard(self)
        self.score_label = QLabel("Score: 0", self)

        # Connect the board's score_changed signal to the update_score method
        self.tetris_board.score_changed.connect(self.update_score)

        layout = QVBoxLayout()
        layout.addWidget(self.score_label)
        layout.addWidget(self.tetris_board)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_score(self, score):
        """ Update score display. """
        self.score_label.setText(f"Score: {score}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Tetris()
    window.resize(BOARD_WIDTH * TILE_SIZE, BOARD_HEIGHT * TILE_SIZE)
    window.show()
    sys.exit(app.exec())
