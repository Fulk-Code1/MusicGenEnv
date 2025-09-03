import pyaudio
import numpy as np
from PyQt5 import QtWidgets, QtCore
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas

# Аудио параметры
SAMPLE_RATE = 44100
VOLUME = 0.5
BUFFER_SIZE = 1024

class AudioEngine:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_playing = False
        self.synth_type = "stop"
        self.buffer = np.zeros(BUFFER_SIZE)
        self.delay_buffer = np.zeros(int(SAMPLE_RATE * 0.5))
        self.feedback = 0.5

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
        if len(wavetable) == 0:
            wavetable = 0.5 * np.sin(np.linspace(0, 2 * np.pi, 512)) + 0.5 * (2 * (np.linspace(0, 1, 512) - 0.5))
        return VOLUME * np.interp(phase, np.linspace(0, 2 * np.pi, len(wavetable)), wavetable)

    def apply_delay(self, data):
        output = np.zeros(len(data), dtype=np.float32)
        for i in range(len(data)):
            output[i] = data[i] + self.feedback * self.delay_buffer[i]
            self.delay_buffer[i] = data[i]
        self.delay_buffer = np.roll(self.delay_buffer, -len(data))
        self.delay_buffer[-len(data):] = 0
        return output

    def callback(self, in_data, frame_count, time_info, status):
        if self.synth_type == "sine":
            data = self.generate_sine(frame_count, 440)
        elif self.synth_type == "fm":
            data = self.generate_fm(frame_count, 440, 100, 5)
        elif self.synth_type == "wavetable":
            data = self.generate_wavetable(frame_count, 440, [])
        else:
            data = np.zeros(frame_count, dtype=np.float32)
        data = self.apply_delay(data)
        self.buffer = np.roll(self.buffer, -frame_count)
        self.buffer[-frame_count:] = data[:frame_count]
        return (data.astype(np.float32).tobytes(), pyaudio.paContinue)

    def set_synth_type(self, synth_type):
        if self.synth_type != synth_type:  # Переключаем только при изменении типа
            if self.is_playing and self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.synth_type = synth_type
            if synth_type != "stop":
                self.stream = self.p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    output=True,
                    stream_callback=self.callback
                )
                self.stream.start_stream()
                self.is_playing = True
            elif synth_type == "stop" and self.is_playing:
                self.stream.stop_stream()
                self.stream.close()
                self.is_playing = False

    def terminate(self):
        if self.stream:
            self.stream.close()
        self.p.terminate()

    def get_buffer(self):
        return self.buffer

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_engine = AudioEngine()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("MusicGenEnv Prototype")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # График
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_ylim(-1, 1)
        self.ax.set_title("Waveform")
        self.layout.addWidget(self.canvas)

        # Кнопки
        self.play_sine = QtWidgets.QPushButton("Play Sine")
        self.play_fm = QtWidgets.QPushButton("Play FM")
        self.play_wavetable = QtWidgets.QPushButton("Play Wavetable")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.layout.addWidget(self.play_sine)
        self.layout.addWidget(self.play_fm)
        self.layout.addWidget(self.play_wavetable)
        self.layout.addWidget(self.stop_button)

        # Подключение кнопок
        self.play_sine.clicked.connect(lambda: self.audio_engine.set_synth_type("sine"))
        self.play_fm.clicked.connect(lambda: self.audio_engine.set_synth_type("fm"))
        self.play_wavetable.clicked.connect(lambda: self.audio_engine.set_synth_type("wavetable"))
        self.stop_button.clicked.connect(lambda: self.audio_engine.set_synth_type("stop"))

        # Обновление графика
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)

    def update_plot(self):
        if self.audio_engine.is_playing:
            self.ax.clear()
            self.ax.plot(self.audio_engine.get_buffer())
            self.ax.set_ylim(-1, 1)
            self.ax.set_title("Waveform")
            self.canvas.draw()

    def closeEvent(self, event):
        self.audio_engine.terminate()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()