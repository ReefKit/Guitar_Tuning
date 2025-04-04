"""
    tuning_utils.py

    This module contains utility functions for handling and analyzing guitar tunings.
    These functions help calculate pitch differences, compare tunings, and determine
    whether two tunings are 'close' based on predefined thresholds. Instead of using 
    modular arithmetic (mod 12) with an octave parameter, we use absolute pitch values 
    (e.g., C1 = 0, C3 = 24), which allows more precise transposition handling.

    The weighting function for closeness evaluation is embedded in the transposition
    optimizer, which uses the L1-norm minimized by the median shift.

    All tunings are assumed to be in low-to-high string order (e.g., E A D G B E).
"""

import numpy as np

# Mapping of musical notes to semitone values for pitch calculations.
NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "E#": 5, "Fb": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0
}

def get_absolute_pitch(tuning: str) -> list:
    """
    Converts a tuning into absolute pitch values, assuming adjacent strings are
    at most an octave apart and at least a semitone apart.

    Args:
        tuning (str): The tuning as a space-separated string (e.g., "E A D G B E").

    Returns:
        list[int]: A list of absolute pitch values.
    """
    strings = [note.strip().capitalize() for note in tuning.split()] # Normalise

    # Validate that all notes are known
    for note in strings:
        if note not in NOTE_TO_SEMITONE:
            raise ValueError(f"Unknown note: '{note}' in tuning '{tuning}'")

    abs_pitches = [NOTE_TO_SEMITONE[strings[0]]]  # First string starts at base pitch
    
    for i in range(1, len(strings)):
        prev_pitch = abs_pitches[-1]
        curr_pitch = NOTE_TO_SEMITONE[strings[i]]

        # Raise current pitch if needed to maintain ascending order
        while curr_pitch <= prev_pitch:
            curr_pitch += 12

        abs_pitches.append(curr_pitch)
    
    return abs_pitches

def optimize_transposition(tuning1: str, tuning2: str) -> int:
    """
    Determines the optimal semitone transposition that minimizes the sum of absolute
    differences between two tunings.

    This function calculates the optimal transposition by finding the median of the
    differences between corresponding strings of the two tunings. The median minimizes
    the sum of absolute deviations, providing the most effective transposition value.

    Args:
        tuning1 (str): The first tuning (e.g., "E A D G B E").
        tuning2 (str): The second tuning (e.g., "D A D G B E").

    Returns:
        int: The optimal transposition amount in semitones.

    Raises:
        ValueError: If the tunings do not have the same number of strings.
    """
    abs_pitch1 = get_absolute_pitch(tuning1)
    abs_pitch2 = get_absolute_pitch(tuning2)
    
    if len(abs_pitch1) != len(abs_pitch2):
        raise ValueError("Tunings must have the same number of strings")
    
    # Calculate the differences between corresponding strings
    differences = [p2 - p1 for p1, p2 in zip(abs_pitch1, abs_pitch2)]
    return int(np.median(differences))

def are_tunings_close(
    tuning1: str,
    tuning2: str,
    max_changed_strings: int,
    max_pitch_change: int,
    max_total_difference: int
) -> tuple[bool, int]:
    """
    Evaluates whether two tunings are 'close' by determining the optimal transposition
    and assessing the number of changed strings, per-string pitch shifts, and total
    pitch shift across all strings.

    Args:
        tuning1 (str): The first tuning (e.g., "E A D G B E").
        tuning2 (str): The second tuning (e.g., "D A D G B E").
        max_changed_strings (int): Maximum number of allowed string changes.
        max_pitch_change (int): Maximum semitone change per string.
        max_total_difference (int): Maximum total pitch difference allowed across all strings.

    Returns:
        Tuple[bool, int]: 
            - True if the tunings are close under optimal transposition, False otherwise.
            - The optimal shift (in semitones).
    """
    shift = optimize_transposition(tuning1, tuning2)
    abs_pitch1 = [p + shift for p in get_absolute_pitch(tuning1)]
    abs_pitch2 = get_absolute_pitch(tuning2)

    differences = [abs(p1 - p2) for p1, p2 in zip(abs_pitch1, abs_pitch2)]

    changed_strings = sum(1 for diff in differences if diff > 0)
    total_difference = sum(differences)

    is_close = (
        changed_strings <= max_changed_strings and
        all(diff <= max_pitch_change for diff in differences) and
        total_difference <= max_total_difference
    )

    return is_close, shift

def get_pitch_vector(tuning1: str, tuning2: str, shift: int) -> list[int]:
    """
    Computes the per-string pitch differences between two tunings after applying
    a global transposition (shift) to tuning1 to best align it with tuning2.

    This function assumes the tunings have already been validated to have the same
    number of strings, and that the optimal shift has been precomputed using
    `optimize_transposition()`.

    Args:
        tuning1 (str): The source tuning (e.g., "E A D G B E").
        tuning2 (str): The destination tuning (e.g., "D A D G B E").
        shift (int): The optimal semitone shift applied to tuning1.

    Returns:
        list[int]: A list of semitone changes for each string, from tuning1 (shifted) to tuning2.
                   For example: [0, 0, -2, 0, 0, 0] means only the 3rd string dropped 2 semitones.
    """
    abs_pitch1 = [p + shift for p in get_absolute_pitch(tuning1)]
    abs_pitch2 = get_absolute_pitch(tuning2)

    return [p2 - p1 for p1, p2 in zip(abs_pitch1, abs_pitch2)] # todo: optimise (this computation is already half done in optimize_transposition)
