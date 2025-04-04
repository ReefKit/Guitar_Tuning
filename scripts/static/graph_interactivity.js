let gigsetPath = [];
let highlightColor = '#90ee90';
let selectedColor = '#ff69b4';
let defaultColor = '#00bfff';
let showSongs = false;

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

function updateHighlighting() {
    const allNodes = network.body.data.nodes.get();
    const updatedNodes = allNodes.map((node, index) => {
        const id = node.id;
        let color = defaultColor;
        let label = showSongs ? node.songs_label : node.tuning_label || node.label;

        if (gigsetPath.includes(id)) {
            color = selectedColor;
            const order = gigsetPath.indexOf(id) + 1;
            label = `${label}`; // Label stays clean, no numbering here
        } else if (
            gigsetPath.length === 0 ||
            getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(id)
        ) {
            color = highlightColor;
        }

        return { id: id, color: color, label: label }; // Label unchanged
    });

    network.body.data.nodes.update(updatedNodes);

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

    // Add numeric overlay for each node
    const canvas = network.canvas.frame.canvas;
    const ctx = canvas.getContext("2d");
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

        if (gigsetPath[gigsetPath.length - 1] === nodeId) {
            gigsetPath.pop(); // Undo last node
        } else if (
            !gigsetPath.includes(nodeId) &&
            (gigsetPath.length === 0 || getAdjacentNodes(gigsetPath[gigsetPath.length - 1]).includes(nodeId))
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

// Initial color setup
network.once("afterDrawing", updateHighlighting);
