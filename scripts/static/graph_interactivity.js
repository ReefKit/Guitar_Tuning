let gigsetPath = [];
let highlightColor = '#90ee90';
let selectedColor = '#ff69b4';
let defaultColor = '#00bfff';
let showSongs = false;
const minPitchPerString = [40-4, 45-4, 50-4, 55-4, 59-4, 64-4];
const maxPitchPerString = [40, 45, 50, 55, 59, 64];

const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

function midiToNote(midiNumber) {
    const note = NOTE_NAMES[midiNumber % 12];
    const octave = Math.floor(midiNumber / 12) - 1;
    return note + octave;
}

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


function getAdjacentNodes(nodeId) {
    const connectedEdges = network.getConnectedEdges(nodeId);
    const adjacent = new Set();
    connectedEdges.forEach(edgeId => {
        const edge = network.body.edges[edgeId];
        const {from, to} = edge;
        if (from.id === nodeId) adjacent.add(to.id);
        else if (to.id === nodeId) adjacent.add(from.id);
    });
    return Array.from(adjacent);
}

let cachedAbsolutePitches = [];

function updateHighlighting() {
    console.log("🔁 updateHighlighting() running with gigsetPath:", gigsetPath);

    const allNodes = network.body.data.nodes.get();
    cachedAbsolutePitches = simulateAbsolutePitches(gigsetPath) || [];
    if (cachedAbsolutePitches.length === 0 && gigsetPath.length > 0) {
        console.warn("🚨 No pitches computed despite gigsetPath existing!");
    }
    // ✅ Map node IDs to pitch sets (fixes the off-by-one bug)
    const pitchMap = {};
    gigsetPath.forEach((id, i) => {
        pitchMap[id] = cachedAbsolutePitches[i];
    });

    const updatedNodes = allNodes.map((node) => {
        const id = node.id;
        let color = defaultColor;
        let label = showSongs ? node.songs_label : node.tuning_label || node.label;
        let font = { color: "white" };
        
        const isSelected = gigsetPath.includes(id); // debug
        const isAdjacent = gigsetPath.length === 0 || getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(id); // debug
        if (isAdjacent && !gigsetPath.includes(id)) {
            const isAllowed = canAddNode(id);
            console.log(`🟡 Adjacent node ${id}: ${isAllowed ? '✅ ALLOWED' : '❌ BLOCKED'}`);
        }
        
        if (gigsetPath.includes(id)) {
            color = selectedColor;

            if (!showSongs) {
                const pitchSet = pitchMap[id];
                if (pitchSet && pitchSet.length === 6 && pitchSet.every(n => !isNaN(n))) {
                    label = pitchSet.map(midiToNote).join(" ");
                    font = { color: selectedColor, bold: true };
                } else {
                    console.warn("⚠️ Invalid or missing pitch set for node", id, pitchSet);
                }
            }
        } else {
            const isAdjacent = gigsetPath.length === 0 || getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(id);
            if (!isAdjacent) {
                color = defaultColor; // blue
            } else if (canAddNode(id)) {
                color = highlightColor; // green
            } else {
                color = '#aaaaaa'; // grey
            }

            // Reset font in tuning mode when not selected
            if (!showSongs) {
                font = { color: "white" };
            }
        }

        if (isSelected || isAdjacent) {
            console.log("Relevant node", id, label);
        } // debug
        
        return { id, color, label, font };
    });

    network.body.data.nodes.update(updatedNodes);

    // 🎯 Update edge highlighting
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

    // 🔢 Number overlay
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


function handleGigsetClick(params) {
    if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];

        // Allow undoing the last node
        if (gigsetPath[gigsetPath.length - 1] === nodeId) {
            gigsetPath.pop();
        } 
        // Only allow adding if node is adjacent AND satisfies constraints
        else if (
            !gigsetPath.includes(nodeId) &&
            (gigsetPath.length === 0 || getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(nodeId)) &&
            canAddNode(nodeId)
        ) {
            gigsetPath.push(nodeId);
        }

        updateHighlighting();
    }
}


function showGigset() {
    alert("Gigset Tunings: " + gigsetPath.join(" -> "));
}

function resetGigset() {
    gigsetPath = [];
    updateHighlighting();
    network.redraw();
}

function toggleLabels() {
    showSongs = !showSongs;
    updateHighlighting();
}

network.on("click", handleGigsetClick);

const showBtn = document.createElement("button");
showBtn.innerHTML = "Show Gigset";
showBtn.style.position = "absolute";
showBtn.style.top = "10px";
showBtn.style.left = "10px";
showBtn.style.zIndex = 9999;
showBtn.onclick = showGigset;
document.body.appendChild(showBtn);

const resetBtn = document.createElement("button");
resetBtn.innerHTML = "Reset Gigset";
resetBtn.style.position = "absolute";
resetBtn.style.top = "50px";
resetBtn.style.left = "10px";
resetBtn.style.zIndex = 9999;
resetBtn.onclick = resetGigset;
document.body.appendChild(resetBtn);

const toggleBtn = document.createElement("button");
toggleBtn.innerHTML = "Toggle Song Labels";
toggleBtn.style.position = "absolute";
toggleBtn.style.top = "90px";
toggleBtn.style.left = "10px";
toggleBtn.style.zIndex = 9999;
toggleBtn.onclick = toggleLabels;
document.body.appendChild(toggleBtn);

const constraintPanel = document.createElement("div");
constraintPanel.style.position = "absolute";
constraintPanel.style.top = "140px";
constraintPanel.style.left = "10px";
constraintPanel.style.backgroundColor = "white";
constraintPanel.style.border = "1px solid #ccc";
constraintPanel.style.padding = "10px";
constraintPanel.style.zIndex = 9999;

constraintPanel.innerHTML = "<b>Pitch Constraints</b><br>";

const stringLabels = ["6 (Low E)", "5 (A)", "4 (D)", "3 (G)", "2 (B)", "1 (High E)"];
const minInputs = [];
const maxInputs = [];

for (let i = 0; i < 6; i++) {
    const label = document.createElement("div");
    label.innerText = `String ${stringLabels[i]}:`;

    const minInput = document.createElement("input");
    minInput.type = "text";
    minInput.value = midiToNote(minPitchPerString[i]);
    minInput.style.width = "60px";
    minInput.onchange = () => {
        const midi = noteToMidi(minInput.value);
        if (midi !== null) {
            minPitchPerString[i] = midi;
            console.log("Updated min constraints:", minPitchPerString.map(midiToNote));
            minInput.style.borderColor = "";
            updateHighlighting();
        } else {
            minInput.style.borderColor = "red";
        }
    };

    const maxInput = document.createElement("input");
    maxInput.type = "text";
    maxInput.value = midiToNote(maxPitchPerString[i]);
    maxInput.style.width = "60px";
    maxInput.onchange = () => {
        const midi = noteToMidi(maxInput.value);
        if (midi !== null) {
            maxPitchPerString[i] = midi;
            console.log("Updated max constraints:", maxPitchPerString.map(midiToNote));
            maxInput.style.borderColor = "";
            updateHighlighting();
        } else {
            maxInput.style.borderColor = "red";
        }
    };

    const row = document.createElement("div");
    row.style.marginBottom = "4px";
    row.appendChild(label);
    row.appendChild(document.createTextNode("Min: "));
    row.appendChild(minInput);
    row.appendChild(document.createTextNode(" Max: "));
    row.appendChild(maxInput);

    constraintPanel.appendChild(row);
}
document.body.appendChild(constraintPanel);


// Initial color setup
network.once("afterDrawing", updateHighlighting);

function getPitchVector(fromId, toId) {
    try {
        const edgeId = network.getConnectedEdges(fromId).find(eid => {
            const edge = network.body.data.edges.get(eid);
            return (
                (edge.from === fromId && edge.to === toId) ||
                (edge.to === fromId && edge.from === toId)
            );
        });

        if (!edgeId) {
            console.warn("No edge found between", fromId, toId);
            return null;
        }

        const edge = network.body.data.edges.get(edgeId);
        const raw = edge.pitch_vector;

        if (!raw) {
            console.warn("No pitch_vector found on edge", edgeId, edge);
            return null;
        }

        const vector = raw.split(',').map(Number);

        // ✅ The fix: assume edges are directed FROM → TO
        return (edge.from === fromId) ? vector : vector.map(x => -x);
    } catch (err) {
        console.error("getPitchVector() failed for", fromId, toId, err);
        return null;
    }
}

function getPitchVector(fromId, toId) {
    try {
        const edgeId = network.getConnectedEdges(fromId).find(eid => {
            const edge = network.body.data.edges.get(eid);
            return (
                (edge.from === fromId && edge.to === toId) ||
                (edge.to === fromId && edge.from === toId)
            );
        });

        if (!edgeId) {
            console.warn("No edge found between", fromId, toId);
            return null;
        }

        const edge = network.body.data.edges.get(edgeId);
        const raw = edge.pitch_vector;

        console.log("Inspecting edge options:", edge.options);
        console.log("raw pitch_vector =", raw, "typeof =", typeof raw);
        if (!raw) {
            console.warn("No pitch_vector found on edge", edgeId, edge);
            return null;
        }

        const vector = raw.split(',').map(Number);

        // ✅ Corrected check
        return (edge.from === fromId && edge.to === toId) ? vector : vector.map(x => -x);
    } catch (err) {
        console.error("getPitchVector() failed for", fromId, toId, err);
        return null;
    }
}


function simulateAbsolutePitches(path) {
    const pitches = [];

    // Start with EADGBE (standard tuning)
    const node = network.body.data.nodes.get(path[0]);
    console.log("🌐 simulateAbsolutePitches(): node[0] = ", node); // debug
    if (!node || !node.tuning_label) {
        console.warn("Cannot simulate pitches: first node tuning missing");
        return null;
    }
    
    if (!node || !node.tuning_label) {
        console.warn("No tuning_label on first node:", node);
        return null;
    }
    
    let relativeTuning = parseMonotonicTuning(node.tuning_label);
    if (!relativeTuning) return null;

    
    // Now determine max T such that tᵢ + T ∈ [minᵢ, maxᵢ] for all i
    let lower = -Infinity;
    let upper = Infinity;
    
    for (let i = 0; i < 6; i++) {
        const t_i = relativeTuning[i];
        const low = minPitchPerString[i] - t_i;
        const high = maxPitchPerString[i] - t_i;
        lower = Math.max(lower, low);
        upper = Math.min(upper, high);
    }
    
    if (lower > upper) {
        console.warn("⚠️ First tuning cannot be transposed into constraints:", relativeTuning);
        return null;
    }
    
    // Pick max transposition T that fits
    const transposition = Math.floor(upper);
    console.log(`🎯 Initial transposition selected: T = ${transposition}`);
    let current = relativeTuning.map(x => x + transposition);
    pitches.push([...current]);

    for (let i = 1; i < path.length; i++) {
        const fromId = path[i - 1];
        const toId = path[i];
        const vector = getPitchVector(fromId, toId);
        if (!vector) {
            console.warn(`❌ getPitchVector(${fromId}, ${toId}) failed`);
            return null;
        }
    
        console.log(`🧮 Applying vector from ${fromId} → ${toId}:`, vector); // ← add this
        current = current.map((p, idx) => p + vector[idx]);
        pitches.push([...current]);
    }    

    return pitches;
}

function isTranspositionPossible(pitches) {
    console.log("🧪 Checking pitch constraints for path:");

    if (pitches.some(p => p === null)) {
        console.warn("⚠️ One or more tunings failed to simulate. Aborting constraint check.");
        return false;
    }

    console.log("  Path pitches (as notes):");
    pitches.forEach((row, i) => {
        console.log(`    Tuning ${i + 1}:`, row.map(midiToNote));
    });

    console.log("  Allowed pitch ranges:");
    for (let i = 0; i < 6; i++) {
        console.log(`    String ${i + 1}: ${midiToNote(minPitchPerString[i])} – ${midiToNote(maxPitchPerString[i])}`);
    }

    let globalLowerBound = -Infinity;
    let globalUpperBound = Infinity;

    for (let stringIdx = 0; stringIdx < 6; stringIdx++) {
        const stringPitches = pitches.map(tuning => tuning[stringIdx]);

        for (const pitch of stringPitches) {
            const lower = minPitchPerString[stringIdx] - pitch;
            const upper = maxPitchPerString[stringIdx] - pitch;

            globalLowerBound = Math.max(globalLowerBound, lower);
            globalUpperBound = Math.min(globalUpperBound, upper);

            console.log(`    String ${stringIdx + 1}, Pitch ${midiToNote(pitch)}: shift window [${lower}, ${upper}]`);
        }
    }

    console.log("  Final allowed global transposition window:", globalLowerBound, "to", globalUpperBound);

    return globalLowerBound <= globalUpperBound;
}




function canAddNode(candidateId) {
    console.log(`💡 Trying to add node ${candidateId} to gigsetPath: [${gigsetPath.join(" → ")}]`);

    // Always allowed if it's the first node
    if (gigsetPath.length === 0) {
        console.log("🟢 First node — always allowed.");
        return true;
    }

    const lastId = gigsetPath[gigsetPath.length - 1];
    const isAdjacent = getAdjacentNodes(lastId).includes(candidateId);

    if (!isAdjacent) {
        console.log(`🔒 Node ${candidateId} is not adjacent to ${lastId}`);
        return false;
    }

    const simulatedPath = [...gigsetPath, candidateId];
    const pitches = simulateAbsolutePitches(simulatedPath);

    if (!pitches) {
        console.warn("❌ simulateAbsolutePitches returned null – constraints likely failed");
        console.warn("🔎 simulateAbsolutePitches failed for path:", simulatedPath);
        return false;
    }

    const result = isTranspositionPossible(pitches);
    console.log("✅ isTranspositionPossible result:", result);
    return result;
}



function parseMonotonicTuning(tuningLabel) {
    const rawNotes = tuningLabel.trim().split(/\s+/);
    let pitchClasses = [];

    for (let note of rawNotes) {
        const midi = noteToMidi(note + "0");
        if (midi === null) {
            console.error("❌ Invalid note:", note);
            return null;
        }
        pitchClasses.push(midi % 12);
    }

    let pitches = [];
    let prev = -Infinity;

    for (let pc of pitchClasses) {
        // Try octaves from 0 upward
        let octave = 0;
        while ((octave * 12 + pc) <= prev) {
            octave++;
        }
        let midiPitch = octave * 12 + pc;
        pitches.push(midiPitch);
        prev = midiPitch;
    }

    return pitches;
}
