from ev3dev2.sound import Sound

spkr = Sound()

def amogus(tempo):
    spkr.play_song((
        ("C3", "q"),

        ("C4", "e"),
        ("Eb4", "e"),
        ("F4", "e"),
        ("Gb4", "e"),
        ("F4", "e"),
        ("Eb4", "e"),
        ("C4", "e"),
        ("R", "q"),
        ("Bb3", "s"),
        ("D4", "s"),
        ("C4", "e"),

        # ("R", "q"),
        # ("G1", "e"),
        # ("C3", "q"),

        # ("C4", "e"),
        # ("Eb4", "e"),
        # ("F4", "e"),
        # ("Gb4", "e"),
        # ("F4", "e"),
        # ("Eb4", "e"),
        # ("Gb4", "e"),
        # ("R", "e"),
        # ("Gb4", "e3"),
        # ("F4", "e3"),
        # ("Eb4", "e3"),
        # ("Gb4", "e3"),
        # ("F4", "e3"),
        # ("Eb4", "e3"),
        # ("C3", "q"),
    ), tempo)
    # speak("Welcome to A moe gus Bot. We hope you enjoy your experience with us.")