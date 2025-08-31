import pyaudio
import numpy as np
from PyQt5 import QtWidgets, QtCore
import sys

# Аудио параметры
SAMPLE_RATE = 44100  # Частота дискретизации
FREQUENCY = 440  # Частота звука (Ля)
VOLUME = 0.5  # Громкость (0.0 - 1.0)

class AudioEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_playing = False

    def callback(self, in_data, frame_count, time_info, status):
        # Генерация синусоиды
        t = np.linspace(0, frame_count / SAMPLE_RATE, frame_count, False)
        data = (VOLUME * np.sin(2 * np.pi * FREQUENCY * t)).astype(np.float32)
        return (data.tobytes(), pyaudio.paContinue)

    def start_stream(self):
        if not self.is_playing:
            self.stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                output=True,
                stream_callback=self.callback
            )
            self.stream.start_stream()
            self.is_playing = True

    def stop_stream(self):
        if self.is_playing and self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.is_playing = False

    def terminate(self):
        self.p.terminate()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_engine = AudioEngine()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MusicGenEnv Prototype")
        self.setGeometry(100, 100, 400, 200)

        # Центральный виджет
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Кнопки
        self.play_button = QtWidgets.QPushButton("Play Tone")
        self.stop_button = QtWidgets.QPushButton("Stop Tone")
        self.layout.addWidget(self.play_button)
        self.layout.addWidget(self.stop_button)

        # Подключение кнопок
        self.play_button.clicked.connect(self.audio_engine.start_stream)
        self.stop_button.clicked.connect(self.audio_engine.stop_stream)

    def closeEvent(self, event):
        self.audio_engine.stop_stream()
        self.audio_engine.terminate()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()