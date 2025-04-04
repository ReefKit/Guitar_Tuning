// =====================================================
// Global State and Configuration
// =====================================================

/**
 * Stores the currently selected path of tunings in the gigset.
 * Each element is a node ID corresponding to a tuning.
 */
let gigsetPath = [];

/**
 * UI color settings for different node states in the graph.
 */
let highlightColor = '#90ee90';    // Green – valid adjacent nodes
let selectedColor = '#ff69b4';     // Pink – selected nodes in gigset
let defaultColor = '#00bfff';      // Blue – unselected nodes

/**
 * Determines whether song labels or tuning labels are shown.
 * true → show song names, false → show tuning pitches.
 */
let showSongs = false;

/**
 * User-defined pitch constraints (in MIDI numbers) for each string.
 * These arrays define the allowed pitch range for each string in the tuning.
 * String order: [Low E, A, D, G, B, High E]
 * 
 * Example:
 *   E2 = 40, so 40-4 = 36 means Low E must be at least C#2
 */
const minPitchPerString = [36, 41, 46, 51, 55, 60];
const maxPitchPerString = [40, 45, 50, 55, 59, 64];

/**
 * Maps semitone offsets to note names for MIDI conversion.
 * Index 0 = C, 1 = C#, ..., 11 = B
 */
const NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
];


/**
 * Converts a MIDI pitch number into a human-readable note name with octave.
 *
 * For example:
 *   midiToNote(40) → "E2"
 *   midiToNote(64) → "E4"
 *
 * @param {number} midiNumber - The MIDI pitch number (e.g., 60 = Middle C).
 * @returns {string} The corresponding note name with octave (e.g., "C4").
 */
function midiToNote(midiNumber) {
    const note = NOTE_NAMES[midiNumber % 12];
    const octave = Math.floor(midiNumber / 12) - 1;
    return note + octave;
}


/**
 * Converts a musical note (e.g., "E2", "C#4", "Bb3") into its corresponding MIDI pitch number.
 *
 * MIDI numbers range from 0 (C-1) to 127 (G9). This function parses both sharp (#) and flat (b)
 * accidentals and supports negative and positive octave values.
 *
 * For example:
 *   noteToMidi("C4") → 60
 *   noteToMidi("A#3") → 58
 *   noteToMidi("Eb2") → 39
 *
 * @param {string} note - The note string in scientific pitch notation.
 * @returns {number|null} The MIDI pitch number, or null if the input is invalid.
 */
function noteToMidi(note) {
    const match = /^([A-Ga-g])([#b]?)(-?\d+)$/.exec(note.trim());
    if (!match) return null;

    let [, letter, accidental, octaveStr] = match;
    letter = letter.toUpperCase();
    const octave = parseInt(octaveStr);

    let semitoneOffset = {
        C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11
    }[letter];

    if (accidental === "#") semitoneOffset += 1;
    if (accidental === "b") semitoneOffset -= 1;

    return (octave + 1) * 12 + semitoneOffset;
}



/**
 * Returns a list of node IDs directly connected to the given node.
 *
 * This function looks at all edges connected to the specified node in the Vis.js network
 * and identifies the nodes on the other end of each edge, ensuring that undirected connections
 * are handled symmetrically.
 *
 * @param {string|number} nodeId - The ID of the node to find neighbors for.
 * @returns {Array<string|number>} An array of adjacent node IDs.
 */
function getAdjacentNodes(nodeId) {
    const connectedEdges = network.getConnectedEdges(nodeId);
    const adjacent = new Set();

    connectedEdges.forEach(edgeId => {
        const edge = network.body.edges[edgeId];
        const { from, to } = edge;

        if (from.id === nodeId) adjacent.add(to.id);
        else if (to.id === nodeId) adjacent.add(from.id);
    });

    return Array.from(adjacent);
}


// Cache for absolute pitch values corresponding to each tuning in gigsetPath
let cachedAbsolutePitches = [];

/**
 * Updates the node highlighting in the network graph based on the current gigset path.
 * This function recalculates the pitch values for tunings along the gigset path, adjusts the
 * node colors depending on their adjacency to the path, and updates edge highlighting.
 */
function updateHighlighting() {
    // Retrieve all nodes in the graph
    const allNodes = network.body.data.nodes.get();

    // Simulate absolute pitches along the gigset path
    cachedAbsolutePitches = simulateAbsolutePitches(gigsetPath) || [];

    // Warn if no pitches were computed despite the gigsetPath existing
    if (cachedAbsolutePitches.length === 0 && gigsetPath.length > 0) {
        console.warn("🚨 No pitches computed despite gigsetPath existing!");
    }

    // Map node IDs to their corresponding pitch sets
    const pitchMap = {};
    gigsetPath.forEach((id, i) => {
        pitchMap[id] = cachedAbsolutePitches[i];
    });

    // Update node colors and labels based on their state (selected or adjacent to the path)
    const updatedNodes = allNodes.map((node) => {
        const id = node.id;
        let color = defaultColor; // Default color for nodes
        let label = showSongs ? node.songs_label : node.tuning_label || node.label;
        let font = { color: "white" }; // Default font color

        // Check if the node is selected or adjacent to the path
        const isSelected = gigsetPath.includes(id);
        const isAdjacent = gigsetPath.length === 0 || getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(id);

        // Apply colors and labels for selected nodes
        if (isSelected) {
            color = selectedColor; // Highlight selected node with a special color

            // Update label for selected node to display the absolute pitches in note form
            if (!showSongs) {
                const pitchSet = pitchMap[id];
                if (pitchSet && pitchSet.length === 6 && pitchSet.every(n => !isNaN(n))) {
                    label = pitchSet.map(midiToNote).join(" ");
                    font = { color: selectedColor, bold: true }; // Bold font for selected node
                } else {
                    console.warn("⚠️ Invalid or missing pitch set for node", id, pitchSet);
                }
            }
        } else {
            // Handle unselected nodes, setting color based on adjacency and constraints
            if (!isAdjacent) {
                color = defaultColor; // Blue for non-adjacent nodes
            } else if (canAddNode(id)) {
                color = highlightColor; // Green for adjacent and allowed nodes
            } else {
                color = '#aaaaaa'; // Grey for blocked nodes
            }

            // Reset font to white if it's not a selected node
            if (!showSongs) {
                font = { color: "white" };
            }
        }

        return { id, color, label, font };
    });

    // Update node data with new colors and labels
    network.body.data.nodes.update(updatedNodes);

    // Update edge colors based on whether they are part of the gigset path
    const allEdges = network.body.data.edges.get();
    const updatedEdges = allEdges.map(edge => {
        const fromIndex = gigsetPath.indexOf(edge.from);
        const toIndex = gigsetPath.indexOf(edge.to);
        const isConsecutive = Math.abs(fromIndex - toIndex) === 1;
        const isInPath = fromIndex !== -1 && toIndex !== -1 && isConsecutive;
        return {
            id: edge.id,
            color: isInPath ? { color: '#ff69b4', highlight: '#ff1493' } : { color: '#848484' }
        };
    });
    network.body.data.edges.update(updatedEdges);

    // Add a numbering overlay on the nodes to show the order in the path
    network.on("afterDrawing", () => {
        const canvas = network.canvas.frame.canvas;
        const ctx = canvas.getContext("2d");
        ctx.font = "bold 16px Arial";
        ctx.fillStyle = "black";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        gigsetPath.forEach((nodeId, i) => {
            const pos = network.getPositions([nodeId])[nodeId];
            ctx.fillText(i + 1, pos.x, pos.y);
        });
    });
}


/**
 * Handles a click on a node in the network graph. Allows selecting and deselecting nodes
 * based on adjacency and constraint validation.
 */
function handleGigsetClick(params) {
    if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];

        // Allow undoing the last node if it's already in the gigset path
        if (gigsetPath[gigsetPath.length - 1] === nodeId) {
            gigsetPath.pop();
        } 
        // Add node to gigsetPath if it's adjacent and satisfies the constraints
        else if (
            !gigsetPath.includes(nodeId) &&
            (gigsetPath.length === 0 || getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(nodeId)) &&
            canAddNode(nodeId)
        ) {
            gigsetPath.push(nodeId);
        }

        // Recalculate highlighting based on the updated gigset path
        updateHighlighting();
    }
}


/**
 * Displays the current gigset tunings in an alert message.
 * This function is triggered when the user wants to view the path of selected tunings.
 */
function showGigset() {
    // Show the tunings in the gigset path as a string in the format: "Tuning1 -> Tuning2 -> ..."
    alert("Gigset Tunings: " + gigsetPath.join(" -> "));
}


/**
 * Resets the gigset path by clearing the current sequence of tunings,
 * updating the highlighting of nodes, and redrawing the network to reflect the changes.
 */
function resetGigset() {
    // Clear the current gigset path
    gigsetPath = [];

    // Update the node and edge highlighting based on the empty gigset path
    updateHighlighting();

    // Redraw the network visualization to reflect the reset state
    network.redraw();
}


/**
 * Toggles the visibility of the song labels on the nodes in the network graph.
 * This function switches between displaying song names or tuning labels, depending
 * on the current state, and triggers an update to the node highlighting.
 */
function toggleLabels() {
    // Toggle the showSongs flag between true and false
    showSongs = !showSongs;

    // Update the node highlighting based on the new state of showSongs
    updateHighlighting();
}


/**
 * Sets up the network click handler and UI elements like buttons for interaction.
 * This includes setting up buttons for showing the gigset, resetting the gigset,
 * toggling the song labels, and displaying the pitch constraint panel.
 */

// Add click handler for the network graph (for selecting nodes)
network.on("click", handleGigsetClick);

// Create and style the "Show Gigset" button
const showBtn = document.createElement("button");
showBtn.innerHTML = "Show Gigset";
showBtn.style.position = "absolute";
showBtn.style.top = "10px";
showBtn.style.left = "10px";
showBtn.style.zIndex = 9999;
showBtn.onclick = showGigset; // Trigger showing the current gigset
document.body.appendChild(showBtn);

// Create and style the "Reset Gigset" button
const resetBtn = document.createElement("button");
resetBtn.innerHTML = "Reset Gigset";
resetBtn.style.position = "absolute";
resetBtn.style.top = "50px";
resetBtn.style.left = "10px";
resetBtn.style.zIndex = 9999;
resetBtn.onclick = resetGigset; // Trigger resetting the gigset
document.body.appendChild(resetBtn);

// Create and style the "Toggle Song Labels" button
const toggleBtn = document.createElement("button");
toggleBtn.innerHTML = "Toggle Song Labels";
toggleBtn.style.position = "absolute";
toggleBtn.style.top = "90px";
toggleBtn.style.left = "10px";
toggleBtn.style.zIndex = 9999;
toggleBtn.onclick = toggleLabels; // Toggle between showing songs or tunings
document.body.appendChild(toggleBtn);

// Create and style the panel for pitch constraints
const constraintPanel = document.createElement("div");
constraintPanel.style.position = "absolute";
constraintPanel.style.top = "140px";
constraintPanel.style.left = "10px";
constraintPanel.style.backgroundColor = "white";
constraintPanel.style.border = "1px solid #ccc";
constraintPanel.style.padding = "10px";
constraintPanel.style.zIndex = 9999;

// Add title to the constraints panel
constraintPanel.innerHTML = "<b>Pitch Constraints</b><br>";

// Create string labels for pitch constraint inputs
const stringLabels = ["6 (Low E)", "5 (A)", "4 (D)", "3 (G)", "2 (B)", "1 (High E)"];
const minInputs = [];
const maxInputs = [];


/**
 * Creates and appends input elements for adjusting the pitch constraints
 * of the guitar strings. Each string has a minimum and maximum pitch value
 * that can be adjusted, and any invalid input is visually indicated.
 */
for (let i = 0; i < 6; i++) {
    // Create a label for the current string
    const label = document.createElement("div");
    label.innerText = `String ${stringLabels[i]}:`;

    // Create and set up the minimum pitch input field
    const minInput = document.createElement("input");
    minInput.type = "text";
    minInput.value = midiToNote(minPitchPerString[i]); // Set the initial value
    minInput.style.width = "60px"; // Set input field width
    minInput.onchange = () => {
        const midi = noteToMidi(minInput.value); // Convert the input to MIDI
        if (midi !== null) {
            // Update the min pitch value if valid
            minPitchPerString[i] = midi;
            minInput.style.borderColor = ""; // Reset border color to default
            updateHighlighting(); // Recalculate and update highlighting
        } else {
            // If invalid input, highlight the field in red
            minInput.style.borderColor = "red";
        }
    };

    // Create and set up the maximum pitch input field
    const maxInput = document.createElement("input");
    maxInput.type = "text";
    maxInput.value = midiToNote(maxPitchPerString[i]); // Set the initial value
    maxInput.style.width = "60px"; // Set input field width
    maxInput.onchange = () => {
        const midi = noteToMidi(maxInput.value); // Convert the input to MIDI
        if (midi !== null) {
            // Update the max pitch value if valid
            maxPitchPerString[i] = midi;
            maxInput.style.borderColor = ""; // Reset border color to default
            updateHighlighting(); // Recalculate and update highlighting
        } else {
            // If invalid input, highlight the field in red
            maxInput.style.borderColor = "red";
        }
    };

    // Create a container (row) for the min and max input fields
    const row = document.createElement("div");
    row.style.marginBottom = "4px"; // Add some space between rows
    row.appendChild(label); // Add string label to the row
    row.appendChild(document.createTextNode("Min: ")); // Add "Min: " text
    row.appendChild(minInput); // Add the minimum pitch input field
    row.appendChild(document.createTextNode(" Max: ")); // Add "Max: " text
    row.appendChild(maxInput); // Add the maximum pitch input field

    // Append the row to the constraint panel
    constraintPanel.appendChild(row);
}

// Append the complete constraint panel to the document body
document.body.appendChild(constraintPanel);

// Initial color setup
network.once("afterDrawing", updateHighlighting);


/**
 * Retrieves the pitch vector representing the transposition from one tuning to another.
 * The pitch vector indicates how each string needs to be transposed to move from one tuning to another.
 * Assumes that edges are directed FROM → TO.
 *
 * @param {string} fromId - The ID of the starting tuning node.
 * @param {string} toId - The ID of the destination tuning node.
 * @returns {Array|null} - The pitch vector as an array of numbers, or null if no valid edge exists.
 */
function getPitchVector(fromId, toId) {
    try {
        // Find the edge connecting the two nodes (fromId to toId)
        const edgeId = network.getConnectedEdges(fromId).find(eid => {
            const edge = network.body.data.edges.get(eid);
            return (
                (edge.from === fromId && edge.to === toId) ||
                (edge.to === fromId && edge.from === toId)
            );
        });

        // If no edge is found, return null
        if (!edgeId) {
            return null;
        }

        const edge = network.body.data.edges.get(edgeId);
        const raw = edge.pitch_vector;

        // If there's no pitch_vector, return null
        if (!raw) {
            return null;
        }

        // Convert the raw pitch vector string into an array of numbers
        const vector = raw.split(',').map(Number);

        // Ensure the direction of the pitch vector is FROM → TO
        return (edge.from === fromId) ? vector : vector.map(x => -x);
    } catch (err) {
        // Handle errors that occur during the process
        return null;
    }
}


/**
 * Simulates the absolute pitches along the given path of tunings.
 * The function calculates the transposition needed to fit each tuning within specified pitch constraints.
 *
 * @param {Array} path - The array of node IDs representing the gigset path.
 * @returns {Array|null} - The array of absolute pitches for each tuning in the path, or null if the path is invalid.
 */
function simulateAbsolutePitches(path) {
    const pitches = [];

    // Retrieve the first node's tuning label
    const node = network.body.data.nodes.get(path[0]);
    if (!node || !node.tuning_label) {
        return null; // Return null if tuning information is missing
    }

    // Parse the relative tuning from the node's tuning label
    let relativeTuning = parseMonotonicTuning(node.tuning_label);
    if (!relativeTuning) return null;

    // Determine the maximum transposition T that fits within the constraints for all strings
    let lower = -Infinity;
    let upper = Infinity;
    for (let i = 0; i < 6; i++) {
        const t_i = relativeTuning[i];
        const low = minPitchPerString[i] - t_i;
        const high = maxPitchPerString[i] - t_i;
        lower = Math.max(lower, low);
        upper = Math.min(upper, high);
    }

    // If the constraints make transposition impossible, return null
    if (lower > upper) {
        return null;
    }

    // Select the maximum transposition T that fits
    const transposition = Math.floor(upper);
    let current = relativeTuning.map(x => x + transposition);
    pitches.push([...current]);

    // Iterate over the path to apply pitch changes from one node to the next
    for (let i = 1; i < path.length; i++) {
        const fromId = path[i - 1];
        const toId = path[i];
        const vector = getPitchVector(fromId, toId);
        if (!vector) {
            return null; // Return null if no valid pitch vector is found
        }
    
        // Apply the pitch vector to adjust the tuning
        current = current.map((p, idx) => p + vector[idx]);
        pitches.push([...current]);
    }

    return pitches; // Return the computed absolute pitches for the path
}


/**
 * Validates if a sequence of tunings in the gigset path satisfies the pitch constraints.
 * The function checks if the sequence of tunings can be transposed such that all tunings fit
 * within the specified minimum and maximum pitch constraints for each string.
 *
 * @param {Array} pitches - An array of tunings, each represented as an array of pitch values for the strings.
 * @returns {boolean} - Returns `true` if the transposition is possible within the constraints, `false` otherwise.
 */
function isTranspositionPossible(pitches) {
    // Check if any tuning simulation failed (i.e., contains null values)
    if (pitches.some(p => p === null)) {
        console.warn("⚠️ One or more tunings failed to simulate. Aborting constraint check.");
        return false;
    }

    let globalLowerBound = -Infinity;
    let globalUpperBound = Infinity;

    // Iterate through each string and check if the tuning is within allowed bounds
    for (let stringIdx = 0; stringIdx < 6; stringIdx++) {
        const stringPitches = pitches.map(tuning => tuning[stringIdx]);

        // For each pitch of a string, calculate the transposition window
        for (const pitch of stringPitches) {
            const lower = minPitchPerString[stringIdx] - pitch;
            const upper = maxPitchPerString[stringIdx] - pitch;

            // Update global bounds based on this string's pitch constraints
            globalLowerBound = Math.max(globalLowerBound, lower);
            globalUpperBound = Math.min(globalUpperBound, upper);
        }
    }

    // Check if the transposition window is valid
    return globalLowerBound <= globalUpperBound;
}


/**
 * Determines whether a node can be added to the gigset path based on adjacency and pitch constraints.
 * The function checks if the node is adjacent to the last node in the path, simulates the absolute pitches
 * along the updated path, and validates if the path satisfies the pitch constraints.
 *
 * @param {string} candidateId - The ID of the node to potentially add to the gigset path.
 * @returns {boolean} - Returns `true` if the node can be added to the gigset path, `false` otherwise.
 */
function canAddNode(candidateId) {
    // Allow the first node to be added regardless of constraints
    if (gigsetPath.length === 0) {
        return true;
    }

    const lastId = gigsetPath[gigsetPath.length - 1];
    const isAdjacent = getAdjacentNodes(lastId).includes(candidateId);

    // If the node is not adjacent, it cannot be added to the path
    if (!isAdjacent) {
        return false;
    }

    // Simulate the path with the candidate node added
    const simulatedPath = [...gigsetPath, candidateId];
    const pitches = simulateAbsolutePitches(simulatedPath);

    // If the simulation fails (returns null), the node is not valid
    if (!pitches) {
        return false;
    }

    // Validate if the path satisfies the pitch constraints
    const result = isTranspositionPossible(pitches);
    return result;
}


/**
 * Parses a tuning label (e.g., "E A D G B E") into a list of absolute pitch values, ensuring
 * that the tuning is in ascending order of pitch. This function converts the note names into
 * MIDI values and calculates the correct octaves to maintain a monotonically increasing pitch sequence.
 *
 * @param {string} tuningLabel - The tuning label as a space-separated string (e.g., "E A D G B E").
 * @returns {Array<number>|null} - Returns an array of absolute pitch values or null if the parsing fails.
 */
function parseMonotonicTuning(tuningLabel) {
    // Split the tuning label into individual notes and convert to MIDI values
    const rawNotes = tuningLabel.trim().split(/\s+/);
    let pitchClasses = [];

    // Convert each note to its corresponding pitch class (mod 12)
    for (let note of rawNotes) {
        const midi = noteToMidi(note + "0");
        if (midi === null) {
            // If an invalid note is found, return null
            return null;
        }
        pitchClasses.push(midi % 12);
    }

    // Calculate the absolute pitch values while maintaining ascending order
    let pitches = [];
    let prev = -Infinity;

    for (let pc of pitchClasses) {
        let octave = 0;

        // Ensure that each note is higher than the previous one by adjusting octaves
        while ((octave * 12 + pc) <= prev) {
            octave++;
        }

        let midiPitch = octave * 12 + pc;
        pitches.push(midiPitch);
        prev = midiPitch;
    }

    return pitches;
}
