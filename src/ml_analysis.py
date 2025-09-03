from music21 import stream, note, chord

def simple_harmonization(melody):
    # Простая гармонизация: добавляем аккорд Cmaj (C-E-G) к каждой ноте
    harmonized = stream.Stream()
    for n in melody:
        if isinstance(n, note.Note):
            chord_instance = chord.Chord([n.nameWithOctave, 'E4', 'G4'])
            harmonized.append(chord_instance)
    return harmonized

# Пример использования
if __name__ == "__main__":
    melody = stream.Stream()
    melody.append(note.Note("C4", quarterLength=1))
    melody.append(note.Note("D4", quarterLength=1))
    result = simple_harmonization(melody)
    result.show('text')