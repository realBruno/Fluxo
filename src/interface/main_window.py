from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Fluxo BitTorrent")

        container = QWidget()
        self.setCentralWidget(container)

        layout = QVBoxLayout(container)

        label1 = QLabel("Fluxo1")
        label2 = QLabel("Fluxo2")
        label3 = QLabel("Fluxo3")
        label4 = QLabel("Fluxo4")
        label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label1)
        layout.addWidget(label2)
        layout.addWidget(label3)
        layout.addWidget(label4)


if __name__ == '__main__':
    app = QApplication()

    window = MainWindow()
    window.show()

    app.exec()