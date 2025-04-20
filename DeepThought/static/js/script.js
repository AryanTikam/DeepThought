let universeCounter = 0;

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  sidebar.classList.toggle("collapsed");
}

async function addUniverse() {
  const universeName = prompt(
    "Enter the name of the universe:",
    `Universe ${universeCounter + 1}`
  );

  if (!universeName) return; // Don't proceed if the user cancels or enters an empty name

  try {
    const formData = new FormData();
    formData.append("name", universeName);

    const response = await fetch("/add-universe", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.success || response.ok) {
      const universeList = document.getElementById("universe-list");
      const universeId = `universe-${universeCounter++}`;

      const universe = document.createElement("div");
      universe.className = "universe";
      universe.setAttribute("draggable", "true");
      universe.id = universeId;
      universe.innerHTML = `<i class="fas fa-globe"></i> <span>${universeName}</span>`;
      universe.addEventListener("click", () =>
        handleUniverseClick(universeId, universeName)
      );

      const fileContainer = document.createElement("div");
      fileContainer.className = "file-container";
      fileContainer.dataset.universeId = universeId;

      universeList.appendChild(universe);
      universeList.appendChild(fileContainer);

      enableDragAndDrop();
    } else {
      alert(`Failed to create universe: ${data.error}`);
    }
  } catch (error) {
    console.error("Error creating universe:", error);
    alert("An error occurred while creating the universe.");
  }
}

async function deleteUniverse() {
  const selected = document.querySelector(".universe.selected");
  if (selected) {
    const universeId = selected.id;

    try {
      const formData = new FormData();
      formData.append("universeId", universeId);

      const response = await fetch("/delete-universe", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        const container = document.querySelector(
          `[data-universe-id="${universeId}"]`
        );
        selected.remove();
        if (container) container.remove();

        // Reset chat output
        document.getElementById("chat-output").innerHTML = `
          <div class="welcome-message">
            <h2><i class="fas fa-robot"></i> Welcome to Universe Chat</h2>
            <p>Create or select a universe to begin exploring possibilities</p>
          </div>
        `;
      } else {
        alert(`Failed to delete universe: ${data.error}`);
      }
    } catch (error) {
      console.error("Error deleting universe:", error);
      alert("An error occurred while deleting the universe.");
    }
  } else {
    alert("Please select a universe to delete.");
  }
}

async function handleUniverseClick(id, name) {
  const allUniverses = document.querySelectorAll(".universe");
  allUniverses.forEach((u) => u.classList.remove("selected"));

  const clicked = document.getElementById(id);
  clicked.classList.add("selected");

  document.getElementById(
    "chat-output"
  ).innerHTML = `<p class="loading-message">📄 Loading files from ${
    name || clicked.textContent.trim()
  }...</p>`;

  try {
    // Get files for this universe
    const response = await fetch(`/get-universe-files?universeId=${id}`);
    const data = await response.json();

    // Show files in the file container
    const fileContainer = document.querySelector(`[data-universe-id="${id}"]`);
    fileContainer.innerHTML = "";
    fileContainer.classList.add("show");

    if (data.files && data.files.length > 0) {
      data.files.forEach((file) => {
        const fileItem = document.createElement("div");
        fileItem.className = "file-item";
        fileItem.innerHTML = `
          <span>${file}</span>
          <button onclick="deleteFile('${id}', '${file}')">
            <i class="fas fa-trash"></i>
          </button>
        `;
        fileContainer.appendChild(fileItem);
      });
    } else {
      fileContainer.innerHTML = `
        <div class="empty-files">
          <p><i class="fas fa-info-circle"></i> No text files in this universe yet.</p>
          <p>Upload .txt files to begin analysis.</p>
        </div>
      `;
    }

    // Update chat output with universe info
    document.getElementById("chat-output").innerHTML = `
      <div class="universe-info">
        <h3><i class="fas fa-globe"></i> ${
          name || clicked.textContent.trim()
        }</h3>
        <p>Select an action from the top bar or upload text files to analyze this universe.</p>
      </div>
    `;
  } catch (error) {
    console.error("Error loading universe files:", error);
    document.getElementById("chat-output").innerHTML = `
      <div class="error-message">
        <h3><i class="fas fa-exclamation-triangle"></i> Error</h3>
        <p>Failed to load universe files. Please try again.</p>
      </div>
    `;
  }
}

async function deleteFile(universeId, filename) {
  try {
    const formData = new FormData();
    formData.append("universeId", universeId);
    formData.append("filename", filename);

    const response = await fetch("/delete-file", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.success) {
      // Refresh the file list
      const fileResponse = await fetch(
        `/get-universe-files?universeId=${universeId}`
      );
      const fileData = await fileResponse.json();

      const fileContainer = document.querySelector(
        `[data-universe-id="${universeId}"]`
      );
      fileContainer.innerHTML = "";

      if (fileData.files && fileData.files.length > 0) {
        fileData.files.forEach((file) => {
          const fileItem = document.createElement("div");
          fileItem.className = "file-item";
          fileItem.innerHTML = `
            <span>${file}</span>
            <button onclick="deleteFile('${universeId}', '${file}')">
              <i class="fas fa-trash"></i>
            </button>
          `;
          fileContainer.appendChild(fileItem);
        });
      } else {
        fileContainer.innerHTML = `
          <div class="empty-files">
            <p><i class="fas fa-info-circle"></i> No text files in this universe yet.</p>
            <p>Upload .txt files to begin analysis.</p>
          </div>
        `;
      }
    } else {
      alert(`Failed to delete file: ${data.error}`);
    }
  } catch (error) {
    console.error("Error deleting file:", error);
    alert("An error occurred while deleting the file.");
  }
}

function enableDragAndDrop() {
  const items = document.querySelectorAll(".universe");
  let dragSrc = null;

  items.forEach((item) => {
    item.addEventListener("dragstart", function (e) {
      dragSrc = this;
      e.dataTransfer.effectAllowed = "move";
    });

    item.addEventListener("dragover", function (e) {
      e.preventDefault();
      return false;
    });

    item.addEventListener("drop", function (e) {
      e.stopPropagation();
      if (dragSrc !== this) {
        const list = document.getElementById("universe-list");
        const filesA = document.querySelector(
          `[data-universe-id="${dragSrc.id}"]`
        );
        const filesB = document.querySelector(
          `[data-universe-id="${this.id}"]`
        );

        list.insertBefore(dragSrc, this);
        list.insertBefore(filesA, filesB);
      }
      return false;
    });
  });
}

// Add event listener to the user input field to close reports when typing
document.getElementById("user-input").addEventListener("input", function() {
  // Check if knowledge graph or contradiction report is displayed
  const chatOutput = document.getElementById("chat-output");
  if (chatOutput.querySelector(".graph-container") || chatOutput.querySelector(".contradiction-report")) {
    // Reset the chat output to a clean state
    chatOutput.innerHTML = `
      <div class="universe-info">
        <h3><i class="fas fa-comment"></i> Chat Mode</h3>
        <p>Type your message and press Enter to send.</p>
      </div>
    `;
  }
});

// Improve the existing sendMessage function to implement actual chat functionality
// Fix the JSON parsing issue in the sendMessage function
function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  const chatOutput = document.getElementById("chat-output");

  // Close any open report first (this is a safety check in addition to the input listener)
  if (chatOutput.querySelector(".graph-container") || chatOutput.querySelector(".contradiction-report")) {
    chatOutput.innerHTML = "";
  }

  // Create user message
  const userMsgDiv = document.createElement("div");
  userMsgDiv.className = "user-message";
  userMsgDiv.innerHTML = `<span class="message-avatar">👤</span> ${message}`;
  chatOutput.appendChild(userMsgDiv);

  // Show typing indicator while waiting for response
  const typingIndicator = document.createElement("div");
  typingIndicator.className = "bot-message typing-indicator";
  typingIndicator.innerHTML = `<span class="message-avatar">🤖</span> <span class="typing-dots">...</span>`;
  chatOutput.appendChild(typingIndicator);

  // Get the active universe path
  const activeUniverse = document.querySelector(".universe.selected");
  const universeId = activeUniverse ? activeUniverse.id : "";
  const universeName = activeUniverse ? activeUniverse.querySelector("span").textContent.trim() : "";
  
  
  // Send message to chat_bot API
  fetch("/call_chat_bot", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      universeId: universeId,
      message: message,
    }),
  })
  .then(response => {
    // First check if response is OK
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    return response.text(); // Get the raw text first
  })
  .then(text => {
    // Try to parse the JSON, with error handling
    try {
      const result = JSON.parse(text);
      // Remove typing indicator
      chatOutput.removeChild(typingIndicator);
      
      // Create bot response message
      const botMsgDiv = document.createElement("div");
      botMsgDiv.className = "bot-message";
      botMsgDiv.innerHTML = `<span class="message-avatar">🤖</span> ${result.answer || "No response received from bot."}`;
      chatOutput.appendChild(botMsgDiv);
    } catch (parseError) {
      console.error("Error parsing JSON:", parseError, "Raw response:", text);
      
      // Handle unparseable response by displaying the raw text
      chatOutput.removeChild(typingIndicator);
      
      const errorMsgDiv = document.createElement("div");
      errorMsgDiv.className = "bot-message";
      errorMsgDiv.innerHTML = `<span class="message-avatar">🤖</span> ${text || "Received unparseable response."}`;
      chatOutput.appendChild(errorMsgDiv);
    }
  })
  .catch(error => {
    // Remove typing indicator
    if (typingIndicator.parentNode) {
      chatOutput.removeChild(typingIndicator);
    }
    
    // Show error message
    const errorMsgDiv = document.createElement("div");
    errorMsgDiv.className = "bot-message error-message";
    errorMsgDiv.innerHTML = `<span class="message-avatar">🤖</span> Sorry, there was an error processing your request: ${error.message}`;
    chatOutput.appendChild(errorMsgDiv);
    console.error("Chat error:", error);
  });

  // Clear input and scroll to bottom
  input.value = "";
  chatOutput.scrollTop = chatOutput.scrollHeight;
}

// Add event listener for pressing Enter to send message
document.getElementById("user-input")?.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
});

async function showKnowledgeGraph() {
  const selectedUniverse = document.querySelector(".universe.selected");

  if (!selectedUniverse) {
    alert("Please select a universe first.");
    return;
  }

  const universeId = selectedUniverse.id;
  const universeName = selectedUniverse.textContent.trim();

  document.getElementById("chat-output").innerHTML = `
    <div class="loading-message">
      <p><i class="fas fa-spinner fa-spin"></i> Loading knowledge graph for ${universeName}...</p>
    </div>
  `;

  try {
    const response = await fetch(
      `/get-knowledge-graph?universeId=${universeId}`
    );
    const data = await response.json();

    if (response.ok && data.knowledge_graph) {
      renderKnowledgeGraph(data, universeName);
    } else {
      document.getElementById("chat-output").innerHTML = `
        <div class="error-message">
          <h3><i class="fas fa-exclamation-triangle"></i> No Knowledge Graph Available</h3>
          <p>Upload text files to this universe to generate a knowledge graph.</p>
        </div>
      `;
    }
  } catch (error) {
    console.error("Error loading knowledge graph:", error);
    document.getElementById("chat-output").innerHTML = `
      <div class="error-message">
        <h3><i class="fas fa-exclamation-triangle"></i> Error</h3>
        <p>Failed to load knowledge graph. Please try again.</p>
      </div>
    `;
  }
}

function renderKnowledgeGraph(data, universeName) {
  const chatOutput = document.getElementById("chat-output");
  const graphData = data.knowledge_graph;

  // Check if we have nodes and edges
  if (!graphData.nodes || !graphData.edges || graphData.nodes.length === 0) {
    chatOutput.innerHTML = `
      <div class="error-message">
        <h3><i class="fas fa-exclamation-triangle"></i> Empty Knowledge Graph</h3>
        <p>No entities or relationships found in this universe.</p>
      </div>
    `;
    return;
  }

  // Calculate additional statistics
  const entityTypes = {};
  graphData.nodes.forEach((node) => {
    if (!entityTypes[node.type]) {
      entityTypes[node.type] = 0;
    }
    entityTypes[node.type]++;
  });

  const relationshipTypes = {};
  graphData.edges.forEach((edge) => {
    if (!relationshipTypes[edge.relationship]) {
      relationshipTypes[edge.relationship] = 0;
    }
    relationshipTypes[edge.relationship]++;
  });

  // Create container for the graph
  chatOutput.innerHTML = `
    <div class="graph-container">
      <h2><i class="fas fa-brain"></i> Knowledge Graph: ${universeName}</h2>
      
      <div class="graph-toolbar">
        <div class="search-wrapper">
          <input type="text" id="node-search" placeholder="Search entities..." class="search-input">
          <button id="search-btn" class="search-btn"><i class="fas fa-search"></i></button>
        </div>
        <div class="view-controls">
          <button id="zoom-in" class="control-btn"><i class="fas fa-search-plus"></i></button>
          <button id="zoom-out" class="control-btn"><i class="fas fa-search-minus"></i></button>
          <button id="reset-view" class="control-btn"><i class="fas fa-sync-alt"></i></button>
        </div>
      </div>
      
      <div class="graph-info">
        <p><strong>${graphData.nodes.length}</strong> entities and <strong>${
    graphData.edges.length
  }</strong> relationships discovered in this universe.</p>
      </div>
      
      <div class="visualization-wrapper">
        <div id="graph-canvas" class="graph-canvas"></div>
        <div class="graph-legend">
          ${Object.keys(entityTypes)
            .map(
              (type) => `
            <div class="legend-item">
              <span class="legend-color" style="background-color: ${getNodeColor(
                type
              )};"></span>
              <span>${type} (${entityTypes[type]})</span>
            </div>
          `
            )
            .join("")}
        </div>
      </div>
      
      <div class="graph-statistics">
        <h3><i class="fas fa-chart-pie"></i> Graph Analysis</h3>
        
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-project-diagram"></i></div>
            <div class="stat-value">${graphData.nodes.length}</div>
            <div class="stat-label">Total Entities</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-link"></i></div>
            <div class="stat-value">${graphData.edges.length}</div>
            <div class="stat-label">Relationships</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-sitemap"></i></div>
            <div class="stat-value">${Object.keys(entityTypes).length}</div>
            <div class="stat-label">Entity Types</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon"><i class="fas fa-code-branch"></i></div>
            <div class="stat-value">${
              Object.keys(relationshipTypes).length
            }</div>
            <div class="stat-label">Relationship Types</div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Initialize the interactive graph
  initializeInteractiveGraph(graphData, "graph-canvas");

  // Add event listeners for the graph controls
  document
    .getElementById("zoom-in")
    .addEventListener("click", () => zoomGraph(1.2));
  document
    .getElementById("zoom-out")
    .addEventListener("click", () => zoomGraph(0.8));
  document
    .getElementById("reset-view")
    .addEventListener("click", resetGraphView);
  document.getElementById("search-btn").addEventListener("click", searchNode);
  document.getElementById("node-search").addEventListener("keypress", (e) => {
    if (e.key === "Enter") searchNode();
  });
}

// Helper function to get node color based on type
function getNodeColor(type) {
  const colorMap = {
    Character: "#4a6cf7",
    Location: "#00d4d7",
    Object: "#ff6b6b",
    Event: "#ffc107",
    Concept: "#8e44ad",
    Organization: "#2ecc71",
  };

  return colorMap[type] || "#6c757d";
}

// Helper function to get top relationships by count
function getTopRelationships(relationshipTypes, limit) {
  return Object.entries(relationshipTypes)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
}

// Helper function to calculate the most central nodes
function getTopCentralNodes(graphData, limit) {
  // Calculate degree centrality (number of connections)
  const centralityScores = {};

  graphData.nodes.forEach((node) => {
    centralityScores[node.id] = {
      id: node.id,
      type: node.type,
      connections: 0,
    };
  });

  graphData.edges.forEach((edge) => {
    if (centralityScores[edge.source]) {
      centralityScores[edge.source].connections++;
    }
    if (centralityScores[edge.target]) {
      centralityScores[edge.target].connections++;
    }
  });

  return Object.values(centralityScores)
    .sort((a, b) => b.connections - a.connections)
    .slice(0, limit);
}

// Global variables for the graph visualization
let graphSimulation;
let graphSvg;
let graphZoom;

// Initialize the interactive D3.js graph
function initializeInteractiveGraph(graphData, containerId) {
  const container = document.getElementById(containerId);
  const width = container.clientWidth;
  const height = 500;

  // Clear any existing SVG
  container.innerHTML = "";

  // Create SVG element
  graphSvg = d3
    .select(`#${containerId}`)
    .append("svg")
    .attr("width", "100%")
    .attr("height", height)
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("preserveAspectRatio", "xMidYMid meet");

  // Add zoom behavior
  graphZoom = d3
    .zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", (event) => {
      graphSvg.select("g").attr("transform", event.transform);
    });

  graphSvg.call(graphZoom);

  // Add a group for all the graph elements
  const g = graphSvg.append("g");

  // Add arrow markers for edges
  graphSvg
    .append("defs")
    .append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 30)
    .attr("refY", 0)
    .attr("orient", "auto")
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999");

  // Create the links (edges)
  const links = g
    .selectAll(".link")
    .data(graphData.edges)
    .enter()
    .append("g")
    .attr("class", "link-group");

  const lines = links
    .append("line")
    .attr("class", "link")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .attr("stroke-width", 2)
    .attr("marker-end", "url(#arrowhead)");

  // Add relationship labels to edges
  links
    .append("text")
    .attr("class", "link-label")
    .attr("font-size", "10px")
    .attr("fill", "#555")
    .attr("text-anchor", "middle")
    .attr("dy", -5)
    .text((d) => d.relationship);

  // Create the nodes
  const nodes = g
    .selectAll(".node")
    .data(graphData.nodes)
    .enter()
    .append("g")
    .attr("class", "node-group")
    .call(
      d3
        .drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended)
    );

  // Add circles for nodes
  nodes
    .append("circle")
    .attr("class", "node")
    .attr("r", 20)
    .attr("fill", (d) => getNodeColor(d.type))
    .attr("stroke", "#fff")
    .attr("stroke-width", 2);

  // Add node labels
  nodes
    .append("text")
    .attr("class", "node-label")
    .attr("text-anchor", "middle")
    .attr("dy", 30)
    .attr("font-size", "12px")
    .attr("fill", "#333")
    .text((d) => d.id);

  // Add tooltips on hover
  nodes.append("title").text((d) => `${d.id} (${d.type})`);

  // Create the force simulation
  graphSimulation = d3
    .forceSimulation(graphData.nodes)
    .force(
      "link",
      d3
        .forceLink(graphData.edges)
        .id((d) => d.id)
        .distance(150)
    )
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(40))
    .on("tick", () => {
      // Update positions on tick
      lines
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      links
        .select("text")
        .attr("x", (d) => (d.source.x + d.target.x) / 2)
        .attr("y", (d) => (d.source.y + d.target.y) / 2);

      nodes.attr("transform", (d) => `translate(${d.x}, ${d.y})`);
    });

  // Functions for node dragging
  function dragstarted(event, d) {
    if (!event.active) graphSimulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) graphSimulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  // Reset view initially
  resetGraphView();
}

// Zoom in or out of the graph
function zoomGraph(scaleFactor) {
  graphSvg.transition().duration(500).call(graphZoom.scaleBy, scaleFactor);
}

// Reset the graph view to fit all nodes
function resetGraphView() {
  const container = document.getElementById("graph-canvas");
  const width = container.clientWidth;
  const height = 500;

  graphSvg
    .transition()
    .duration(750)
    .call(
      graphZoom.transform,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(0.8)
    );
}

// Search for a node in the graph
function searchNode() {
  const searchTerm = document.getElementById("node-search").value.toLowerCase();

  if (!searchTerm) return;

  // Find the node with the matching ID
  const nodes = d3.selectAll(".node-group");
  let found = false;

  nodes.each(function (d) {
    if (d.id.toLowerCase().includes(searchTerm)) {
      // Highlight the found node
      d3.select(this)
        .select("circle")
        .transition()
        .duration(300)
        .attr("r", 30)
        .attr("stroke", "#ff6b6b")
        .attr("stroke-width", 4);

      // Center the view on the found node
      graphSvg
        .transition()
        .duration(750)
        .call(
          graphZoom.transform,
          d3.zoomIdentity
            .translate(
              document.getElementById("graph-canvas").clientWidth / 2 - d.x,
              250 - d.y
            )
            .scale(1.2)
        );

      found = true;

      // Reset the highlighting after a delay
      setTimeout(() => {
        d3.select(this)
          .select("circle")
          .transition()
          .duration(300)
          .attr("r", 20)
          .attr("stroke", "#fff")
          .attr("stroke-width", 2);
      }, 3000);
    }
  });

  if (!found) {
    // Flash the search box to indicate no results
    const searchInput = document.getElementById("node-search");
    searchInput.classList.add("search-no-results");
    setTimeout(() => {
      searchInput.classList.remove("search-no-results");
    }, 500);
  }
}

// Helper function to count node types
function countNodeTypes(nodes, type) {
  return nodes.filter((node) => node.type === type).length;
}

// Updated renderContradictionReport function with improved styling
function renderContradictionReport(data, universeName) {
  const chatOutput = document.getElementById("chat-output");
  const contradictions = data.contradictions || [];
  const speculationBoundaries = data.speculation_boundaries || [];

  // Create HTML for contradictions
  let contradictionsHTML = "";
  if (contradictions.length > 0) {
    contradictionsHTML = `
      <div class="contradictions-section">
        <h3><i class="fas fa-exclamation-triangle"></i> Contradictions Found (${
          contradictions.length
        })</h3>
        <div class="contradictions-list">
          ${contradictions
            .map(
              (c, i) => `
            <div class="contradiction-item">
              <div class="contradiction-header">
                <span class="contradiction-number">Contradiction #${
                  i + 1
                }</span>
                <span class="contradiction-confidence">Confidence: ${(
                  c.confidence * 100
                ).toFixed(0)}%</span>
              </div>
              <div class="contradiction-statements">
                <p class="statement statement-1">"${
                  c.conflicting_statements[0]
                }"</p>
                <div class="contradiction-vs">VS</div>
                <p class="statement statement-2">"${
                  c.conflicting_statements[1]
                }"</p>
              </div>
              <div class="contradiction-description">
                <p><strong>Analysis:</strong> ${c.description}</p>
              </div>
            </div>
          `
            )
            .join("")}
        </div>
      </div>
    `;
  } else {
    contradictionsHTML = `
      <div class="contradictions-section empty">
        <h3><i class="fas fa-check-circle"></i> No Contradictions Found</h3>
        <p>The statements in this universe are consistent with each other.</p>
      </div>
    `;
  }

  // Create HTML for speculation boundaries
  let speculationHTML = "";
  if (speculationBoundaries.length > 0) {
    // Group by category
    const groupedSpeculations = {};
    speculationBoundaries.forEach((item) => {
      if (!groupedSpeculations[item.category]) {
        groupedSpeculations[item.category] = [];
      }
      groupedSpeculations[item.category].push(item);
    });

    speculationHTML = `
      <div class="speculation-section">
        <h3><i class="fas fa-lightbulb"></i> Speculation Analysis</h3>
        <div class="speculation-categories">
          ${Object.keys(groupedSpeculations)
            .map(
              (category) => `
            <div class="speculation-category ${category.toLowerCase()}">
              <h4>${category} Statements (${
                groupedSpeculations[category].length
              })</h4>
              <ul class="speculation-list">
                ${groupedSpeculations[category]
                  .map(
                    (item) => `
                  <li class="speculation-item">
                    <span class="confidence-indicator" style="width: ${
                      item.confidence * 100
                    }%"></span>
                    <span class="speculation-text">"${item.element}"</span>
                    <span class="speculation-confidence">${(
                      item.confidence * 100
                    ).toFixed(0)}%</span>
                  </li>
                `
                  )
                  .join("")}
              </ul>
            </div>
          `
            )
            .join("")}
        </div>
      </div>
    `;
  } else {
    speculationHTML = `
      <div class="speculation-section empty">
        <h3><i class="fas fa-question-circle"></i> No Speculation Analysis Available</h3>
        <p>Add more content to generate speculation boundaries.</p>
      </div>
    `;
  }

  // Combine everything with additional stats section
  chatOutput.innerHTML = `
    <div class="contradiction-report">
      <h2><i class="fas fa-file-alt"></i> Universe Analysis: ${universeName}</h2>
      
      <div class="report-summary">
        <div class="summary-card ${
          contradictions.length > 0 ? "has-issues" : "no-issues"
        }">
          <div class="summary-icon">
            <i class="${
              contradictions.length > 0
                ? "fas fa-exclamation-circle"
                : "fas fa-check-circle"
            }"></i>
          </div>
          <div class="summary-content">
            <div class="summary-title">${contradictions.length} Contradiction${
    contradictions.length !== 1 ? "s" : ""
  }</div>
            <div class="summary-description">
              ${
                contradictions.length > 0
                  ? "Logical conflicts detected"
                  : "No logical conflicts found"
              }
            </div>
          </div>
        </div>
        
        <div class="summary-card">
          <div class="summary-icon">
            <i class="fas fa-lightbulb"></i>
          </div>
          <div class="summary-content">
            <div class="summary-title">${
              speculationBoundaries.length
            } Speculation Elements</div>
            <div class="summary-description">
              Elements analyzed for factuality
            </div>
          </div>
        </div>
      </div>
      
      ${contradictionsHTML}
      ${speculationHTML}
    </div>
  `;
}

function drawGraph(graphData, containerId) {
  // This is a placeholder for D3.js code
  // In a real implementation, you would use D3.js to draw the graph

  const container = document.getElementById(containerId);

  // For now, we'll create a simple SVG visualization
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "500");
  svg.setAttribute("viewBox", "0 0 800 500");

  // Create a simple force-directed graph layout
  const nodeRadius = 40;
  const width = 800;
  const height = 500;

  // Position nodes in a circle
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 2 - nodeRadius * 2;

  // Add nodes
  graphData.nodes.forEach((node, i) => {
    const angle = (i / graphData.nodes.length) * 2 * Math.PI;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    // Node color based on type
    let color;
    switch (node.type) {
      case "Character":
        color = "#4a6cf7";
        break;
      case "Location":
        color = "#00d4d7";
        break;
      case "Object":
        color = "#ff6b6b";
        break;
      default:
        color = "#6c757d";
    }

    // Create node circle
    const circle = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "circle"
    );
    circle.setAttribute("cx", x);
    circle.setAttribute("cy", y);
    circle.setAttribute("r", nodeRadius);
    circle.setAttribute("fill", color);
    circle.setAttribute("stroke", "#fff");
    circle.setAttribute("stroke-width", "2");

    // Add node label
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", x);
    text.setAttribute("y", y);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dominant-baseline", "middle");
    text.setAttribute("fill", "#ffffff");
    text.setAttribute("font-size", "12");
    text.textContent = node.id;

    // Add node to SVG
    svg.appendChild(circle);
    svg.appendChild(text);

    // Store node position for edges
    node.x = x;
    node.y = y;
  });

  // Add edges
  graphData.edges.forEach((edge) => {
    const source = graphData.nodes.find((n) => n.id === edge.source);
    const target = graphData.nodes.find((n) => n.id === edge.target);

    if (source && target) {
      // Create edge line
      const line = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "line"
      );
      line.setAttribute("x1", source.x);
      line.setAttribute("y1", source.y);
      line.setAttribute("x2", target.x);
      line.setAttribute("y2", target.y);
      line.setAttribute("stroke", "#6c757d");
      line.setAttribute("stroke-width", "2");
      line.setAttribute("stroke-opacity", "0.6");

      // Add relationship label
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;

      const text = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text"
      );
      text.setAttribute("x", midX);
      text.setAttribute("y", midY);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("dominant-baseline", "middle");
      text.setAttribute("fill", "#333");
      text.setAttribute("font-size", "10");
      text.setAttribute("font-weight", "bold");
      text.setAttribute("background", "#fff");
      text.textContent = edge.relationship;

      // Add edge components to SVG
      svg.appendChild(line);
      svg.appendChild(text);
    }
  });

  container.appendChild(svg);
}

async function showContradictionReport() {
  const selectedUniverse = document.querySelector(".universe.selected");

  if (!selectedUniverse) {
    alert("Please select a universe first.");
    return;
  }

  const universeId = selectedUniverse.id;
  const universeName = selectedUniverse.textContent.trim();

  document.getElementById("chat-output").innerHTML = `
    <div class="loading-message">
      <p><i class="fas fa-spinner fa-spin"></i> Analyzing contradictions in ${universeName}...</p>
    </div>
  `;

  try {
    const response = await fetch(
      `/get-contradictions?universeId=${universeId}`
    );
    const data = await response.json();

    if (response.ok) {
      renderContradictionReport(data, universeName);
    } else {
      document.getElementById("chat-output").innerHTML = `
        <div class="error-message">
          <h3><i class="fas fa-exclamation-triangle"></i> No Contradiction Report Available</h3>
          <p>Upload text files to this universe to generate a contradiction report.</p>
        </div>
      `;
    }
  } catch (error) {
    console.error("Error loading contradictions:", error);
    document.getElementById("chat-output").innerHTML = `
      <div class="error-message">
        <h3><i class="fas fa-exclamation-triangle"></i> Error</h3>
        <p>Failed to load contradiction report. Please try again.</p>
      </div>
    `;
  }
}

function renderContradictionReport(data, universeName) {
  const chatOutput = document.getElementById("chat-output");
  const contradictions = data.contradictions || [];
  const speculationBoundaries = data.speculation_boundaries || [];

  // Calculate statistics
  const totalContradictions = contradictions.length;
  const highConfidenceContradictions = contradictions.filter(
    (c) => c.confidence >= 0.8
  ).length;
  const mediumConfidenceContradictions = contradictions.filter(
    (c) => c.confidence >= 0.5 && c.confidence < 0.8
  ).length;
  const lowConfidenceContradictions = contradictions.filter(
    (c) => c.confidence < 0.5
  ).length;

  // Create HTML for contradictions
  let contradictionsHTML = "";
  if (contradictions.length > 0) {
    contradictionsHTML = `
      <div class="contradictions-section">
        <div class="section-header">
          <h3><i class="fas fa-exclamation-triangle"></i> Contradictions Analysis</h3>
        </div>
        
        <div class="confidence-distribution">
          <div class="confidence-item high">
            <span class="confidence-label">High Confidence</span>
            <span class="confidence-value">${highConfidenceContradictions}</span>
          </div>
          <div class="confidence-item medium">
            <span class="confidence-label">Medium Confidence</span>
            <span class="confidence-value">${mediumConfidenceContradictions}</span>
          </div>
          <div class="confidence-item low">
            <span class="confidence-label">Low Confidence</span>
            <span class="confidence-value">${lowConfidenceContradictions}</span>
          </div>
        </div>
        
        <div class="contradictions-list">
          ${contradictions
            .map(
              (c, i) => `
            <div class="contradiction-item">
              <div class="contradiction-header">
                <span class="contradiction-number">Issue #${i + 1}</span>
                <span class="contradiction-confidence ${getConfidenceClass(
                  c.confidence
                )}">
                  ${getConfidenceText(c.confidence)} (${(
                c.confidence * 100
              ).toFixed(0)}%)
                </span>
              </div>
              <div class="contradiction-statements">
                <div class="statement-container">
                  <div class="statement-marker">Statement A</div>
                  <p class="statement">"${c.conflicting_statements[0]}"</p>
                </div>
                <div class="contradiction-vs">
                  <div class="vs-line"></div>
                  <div class="vs-text">CONFLICTS WITH</div>
                  <div class="vs-line"></div>
                </div>
                <div class="statement-container">
                  <div class="statement-marker">Statement B</div>
                  <p class="statement">"${c.conflicting_statements[1]}"</p>
                </div>
              </div>
              <div class="contradiction-description">
                <div class="description-header">
                  <i class="fas fa-search"></i> Analysis
                </div>
                <p>${
                  c.description ||
                  "No detailed analysis available for this contradiction."
                }</p>
                ${
                  c.suggested_resolution
                    ? `
                <div class="resolution">
                  <div class="resolution-header">
                    <i class="fas fa-lightbulb"></i> Suggested Resolution
                  </div>
                  <p>${c.suggested_resolution}</p>
                </div>
                `
                    : ""
                }
              </div>
            </div>
          `
            )
            .join("")}
        </div>
      </div>
    `;
  } else {
    contradictionsHTML = `
      <div class="contradictions-section empty">
        <div class="success-message">
          <i class="fas fa-check-circle"></i>
          <h3>No Contradictions Detected</h3>
          <p>All statements in this universe appear to be logically consistent.</p>
        </div>
      </div>
    `;
  }

  // Create HTML for speculation boundaries
  let speculationHTML = "";
  if (speculationBoundaries.length > 0) {
    // Group by category
    const groupedSpeculations = {};
    speculationBoundaries.forEach((item) => {
      if (!groupedSpeculations[item.category]) {
        groupedSpeculations[item.category] = [];
      }
      groupedSpeculations[item.category].push(item);
    });

    speculationHTML = `
      <div class="speculation-section">
        <div class="section-header">
          <h3><i class="fas fa-lightbulb"></i> Speculation & Uncertainty Analysis</h3>
        </div>
        
        <div class="speculation-intro">
          <p>The following elements in your universe have been identified as speculative or uncertain. 
          These may require additional verification or clarification to ensure consistency.</p>
        </div>
        
        <div class="speculation-categories">
          ${Object.keys(groupedSpeculations)
            .map(
              (category) => `
            <div class="speculation-category ${category.toLowerCase()}">
              <div class="category-header">
                <h4>${category}</h4>
                <span class="item-count">${
                  groupedSpeculations[category].length
                } items</span>
              </div>
              <ul class="speculation-list">
                ${groupedSpeculations[category]
                  .map(
                    (item) => `
                  <li class="speculation-item">
                    <div class="confidence-meter">
                      <div class="confidence-fill" style="width: ${
                        item.confidence * 100
                      }%"></div>
                    </div>
                    <div class="speculation-content">
                      <div class="speculation-text">"${item.element}"</div>
                      <div class="speculation-meta">
                        <span class="confidence-value ${getConfidenceClass(
                          item.confidence
                        )}">
                          ${getConfidenceText(item.confidence)} (${(
                      item.confidence * 100
                    ).toFixed(0)}%)
                        </span>
                        ${
                          item.context
                            ? `
                        <div class="speculation-context">
                          <i class="fas fa-info-circle"></i> ${item.context}
                        </div>
                        `
                            : ""
                        }
                      </div>
                    </div>
                  </li>
                `
                  )
                  .join("")}
              </ul>
            </div>
          `
            )
            .join("")}
        </div>
      </div>
    `;
  } else {
    speculationHTML = `
      <div class="speculation-section empty">
        <div class="info-message">
          <i class="fas fa-info-circle"></i>
          <h3>No Speculative Elements Found</h3>
          <p>All elements in this universe appear to be well-established facts.</p>
        </div>
      </div>
    `;
  }

  // Combine everything
  chatOutput.innerHTML = `
    <div class="contradiction-report">
      <div class="report-header">
        <h2><i class="fas fa-file-contract"></i> Universe Consistency Report: ${universeName}</h2>
        <p class="report-subtitle">Analysis of logical consistency and factual certainty</p>
      </div>
      
      <div class="report-summary">
        <div class="summary-card ${
          contradictions.length > 0 ? "warning" : "success"
        }">
          <div class="summary-icon">
            <i class="${
              contradictions.length > 0
                ? "fas fa-exclamation-triangle"
                : "fas fa-check-circle"
            }"></i>
          </div>
          <div class="summary-content">
            <h4>${
              contradictions.length > 0
                ? "Potential Issues Found"
                : "No Issues Detected"
            }</h4>
            <p>${
              contradictions.length > 0
                ? "Review the contradictions below to improve consistency"
                : "Your universe maintains good internal consistency"
            }
            </p>
          </div>
        </div>
        
        <div class="summary-card info">
          <div class="summary-icon">
            <i class="fas fa-lightbulb"></i>
          </div>
          <div class="summary-content">
            <h4>Speculative Content</h4>
            <p>${
              speculationBoundaries.length > 0
                ? `${speculationBoundaries.length} elements require verification`
                : "No uncertain elements detected"
            }
            </p>
          </div>
        </div>
      </div>
      
      ${contradictionsHTML}
      ${speculationHTML}
    </div>
  `;
}

// Helper functions for confidence levels
function getConfidenceClass(confidence) {
  if (confidence >= 0.8) return "high-confidence";
  if (confidence >= 0.5) return "medium-confidence";
  return "low-confidence";
}

function getConfidenceText(confidence) {
  if (confidence >= 0.8) return "High Confidence";
  if (confidence >= 0.5) return "Medium Confidence";
  return "Low Confidence";
}

// Handle file uploads and processing
document
  .getElementById("file-upload")
  .addEventListener("change", handleFileUpload);

async function handleFileUpload(event) {
  const fileList = event.target.files;
  const selectedUniverse = document.querySelector(".universe.selected");
  if (!selectedUniverse) {
    alert("Please select a universe to upload files to.");
    return;
  }

  const universeId = selectedUniverse.id;
  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];

    if (!file.name.endsWith(".txt")) {
      alert(`Only .txt files are supported. Skipping ${file.name}`);
      continue;
    }

    try {
      const formData = new FormData();
      formData.append("universeId", universeId);
      formData.append("file", file);

      const response = await fetch("/upload-file", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        // Refresh the file list
        await handleUniverseClick(universeId);
      } else {
        alert(`Failed to upload ${file.name}: ${data.error}`);
      }
    } catch (error) {
      console.error(`Error uploading ${file.name}:`, error);
      alert(`An error occurred while uploading ${file.name}.`);
    }
  }

  // Clear the file input
  event.target.value = "";
}

// Initialize the app when the DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
  // Initialize any required components
});
