import pyaudio
import numpy as np
from PyQt5 import QtWidgets, QtCore
import sys

# Аудио параметры
SAMPLE_RATE = 44100  # Частота дискретизации
VOLUME = 0.5  # Громкость

class AudioEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_playing = False
        self.synth_type = "sine"  # По умолчанию синусоида

    def generate_sine(self, frame_count, frequency):
        t = np.linspace(0, frame_count / SAMPLE_RATE, frame_count, False)
        return VOLUME * np.sin(2 * np.pi * frequency * t)

    def generate_fm(self, frame_count, carrier_freq, mod_freq, mod_index):
        t = np.linspace(0, frame_count / SAMPLE_RATE, frame_count, False)
        modulation = mod_index * np.sin(2 * np.pi * mod_freq * t)
        return VOLUME * np.sin(2 * np.pi * carrier_freq * t + modulation)

    def generate_wavetable(self, frame_count, frequency, wavetable):
        t = np.linspace(0, frame_count / SAMPLE_RATE, frame_count, False)
        phase = (2 * np.pi * frequency * t) % (2 * np.pi)
        return VOLUME * np.interp(phase, np.linspace(0, 2 * np.pi, len(wavetable)), wavetable)

    def callback(self, in_data, frame_count, time_info, status):
        if self.synth_type == "sine":
            data = self.generate_sine(frame_count, 440)  # Ля, 440 Гц
        elif self.synth_type == "fm":
            data = self.generate_fm(frame_count, 440, 100, 5)  # Carrier 440 Гц, mod 100 Гц, index 5
        elif self.synth_type == "wavetable":
            wavetable = np.sin(np.linspace(0, 2 * np.pi, 512))  # Простая таблица синусов
            data = self.generate_wavetable(frame_count, 440, wavetable)
        else:
            data = np.zeros(frame_count, dtype=np.float32)  # Без звука
        return (data.astype(np.float32).tobytes(), pyaudio.paContinue)

    def set_synth_type(self, synth_type):
        self.synth_type = synth_type
        if self.stream and self.is_playing:
            self.stream.stop_stream()
            self.stream.start_stream()

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

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Кнопки
        self.play_button = QtWidgets.QPushButton("Play Sine")
        self.fm_button = QtWidgets.QPushButton("Play FM")
        self.wave_button = QtWidgets.QPushButton("Play Wavetable")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.layout.addWidget(self.play_button)
        self.layout.addWidget(self.fm_button)
        self.layout.addWidget(self.wave_button)
        self.layout.addWidget(self.stop_button)

        # Подключение кнопок
        self.play_button.clicked.connect(lambda: self.audio_engine.set_synth_type("sine"))
        self.fm_button.clicked.connect(lambda: self.audio_engine.set_synth_type("fm"))
        self.wave_button.clicked.connect(lambda: self.audio_engine.set_synth_type("wavetable"))
        self.stop_button.clicked.connect(self.audio_engine.stop_stream)
        self.audio_engine.start_stream()

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