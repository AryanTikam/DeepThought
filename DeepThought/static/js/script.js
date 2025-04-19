// script.js - Frontend JavaScript for the Fictional Universe Consistency Kit

document.addEventListener('DOMContentLoaded', function() {
    // Tab navigation
    const tabLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const pageTitleElement = document.getElementById('pageTitle');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs and content sections
            tabLinks.forEach(tab => tab.classList.remove('active'));
            contentSections.forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show corresponding content section
            const tabId = this.id;
            const contentId = tabId.replace('Tab', 'Interface');
            document.getElementById(contentId).classList.add('active');
            
            // Update page title
            pageTitleElement.textContent = getPageTitle(tabId);
        });
    });
    
    // Toolbar buttons in chat interface
    document.getElementById('extractToolBtn').addEventListener('click', function() {
        activateTab('elementsTab');
    });
    
    document.getElementById('contradictionToolBtn').addEventListener('click', function() {
        activateTab('contradictionsTab');
    });
    
    document.getElementById('factCheckToolBtn').addEventListener('click', function() {
        activateTab('factCheckTab');
    });
    
    document.getElementById('graphToolBtn').addEventListener('click', function() {
        activateTab('graphTab');
    });
    
    // Chat functionality
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Extract Elements functionality
    const extractElementsBtn = document.getElementById('extractElementsBtn');
    extractElementsBtn.addEventListener('click', extractElements);
    
    // Find Contradictions functionality
    const findContradictionsBtn = document.getElementById('findContradictionsBtn');
    findContradictionsBtn.addEventListener('click', findContradictions);
    
    // Fact Check functionality
    const checkFactBtn = document.getElementById('checkFactBtn');
    checkFactBtn.addEventListener('click', checkFact);
    
    // Knowledge Graph functionality
    const updateGraphBtn = document.getElementById('updateGraphBtn');
    updateGraphBtn.addEventListener('click', updateGraph);
    
    // Open Questions functionality
    const findQuestionsBtn = document.getElementById('findQuestionsBtn');
    findQuestionsBtn.addEventListener('click', findOpenQuestions);
    
    // Search Datasets functionality
    const searchDatasetsBtn = document.getElementById('searchDatasetsBtn');
    searchDatasetsBtn.addEventListener('click', searchDatasets);
    
    // Custom universe input toggle
    document.getElementById('universeForQuestions').addEventListener('change', toggleCustomUniverse);
    document.getElementById('universeForFactCheck').addEventListener('change', toggleCustomUniverse);
    document.getElementById('universeSelector').addEventListener('change', toggleCustomUniverse);
    
    // Depth slider value display
    document.getElementById('depthSlider').addEventListener('input', function() {
        document.getElementById('depthValue').textContent = this.value;
    });
    
    // Load initial data
    loadKnowledgeGraphStats();
    loadCharacterOptions();
    
    // Populate element select for graph
    populateElementSelect();
});

// Helper functions
function getPageTitle(tabId) {
    const titles = {
        'chatTab': 'Chat with Fictional Universe Consistency Kit',
        'elementsTab': 'Extract Narrative Elements',
        'contradictionsTab': 'Find Contradictions',
        'factCheckTab': 'Fact Checker',
        'graphTab': 'Knowledge Graph Explorer',
        'openQuestionsTab': 'Open Questions & Speculation Boundaries',
        'searchDatasetsTab': 'Search Reference Datasets'
    };
    return titles[tabId] || 'Fictional Universe Consistency Kit';
}

function activateTab(tabId) {
    document.getElementById(tabId).click();
}

function toggleCustomUniverse(e) {
    const customDivs = document.querySelectorAll('[id^="customUniverseInput"]');
    customDivs.forEach(div => {
        if (e.target.value === 'custom') {
            div.style.display = 'block';
        } else {
            div.style.display = 'none';
        }
    });
}

// Add typing indicator
function showTypingIndicator() {
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'message-container';
    typingIndicator.id = 'typingIndicator';
    typingIndicator.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Chat functionality
function sendMessage() {
    const message = chatInput.value.trim();
    if (message === '') return;
    
    // Add user message to chat
    addMessage(message, 'user');
    chatInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send to backend
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query_type: 'general',
            content: message,
            universe: document.getElementById('universeSelector').value
        })
    })
    .then(response => response.json())
    .then(data => {
        removeTypingIndicator();
        if (data.error) {
            addMessage(`Error: ${data.error}`, 'bot');
        } else {
            addMessage(data.response, 'bot');
        }
    })
    .catch(error => {
        removeTypingIndicator();
        addMessage(`Sorry, there was an error processing your request: ${error}`, 'bot');
    });
}

function addMessage(text, sender) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';
    
    const messageElement = document.createElement('div');
    messageElement.className = sender === 'user' ? 'user-message message' : 'bot-message message';
    messageElement.textContent = text;
    
    messageContainer.appendChild(messageElement);
    chatMessages.appendChild(messageContainer);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Extract Elements functionality
function extractElements() {
    const sourceName = document.getElementById('sourceName').value;
    const sourceType = document.getElementById('sourceType').value;
    const content = document.getElementById('textContent').value;
    
    if (!sourceName || !content) {
        alert('Please enter both source name and content');
        return;
    }
    
    document.getElementById('extractElementsBtn').disabled = true;
    document.getElementById('extractElementsBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Extracting...';
    
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query_type: 'extract_elements',
            source_name: sourceName,
            source_type: sourceType,
            content: content
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('extractElementsBtn').disabled = false;
        document.getElementById('extractElementsBtn').textContent = 'Extract Elements';
        
        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }
        
        // Show results
        document.getElementById('noElementsMsg').style.display = 'none';
        document.getElementById('extractedElements').style.display = 'block';
        
        // Display characters
        const charactersList = document.getElementById('charactersList');
        charactersList.innerHTML = '';
        if (data.characters && data.characters.length > 0) {
            data.characters.forEach(character => {
                const characterCard = createCardElement(
                    character.name || 'Unnamed Character',
                    `${character.traits ? `<strong>Traits:</strong> ${character.traits}<br>` : ''}
                    ${character.relationships ? `<strong>Relationships:</strong> ${character.relationships}` : ''}`
                );
                charactersList.appendChild(characterCard);
            });
        } else {
            charactersList.innerHTML = '<div class="alert alert-info">No characters found</div>';
        }
        
        // Display locations
        const locationsList = document.getElementById('locationsList');
        locationsList.innerHTML = '';
        if (data.locations && data.locations.length > 0) {
            data.locations.forEach(location => {
                const locationCard = createCardElement(
                    location.name || 'Unnamed Location',
                    location.description || 'No description available'
                );
                locationsList.appendChild(locationCard);
            });
        } else {
            locationsList.innerHTML = '<div class="alert alert-info">No locations found</div>';
        }
        
        // Display timeline events
        const eventsList = document.getElementById('eventsList');
        eventsList.innerHTML = '';
        if (data.timeline_events && data.timeline_events.length > 0) {
            data.timeline_events.forEach(event => {
                const eventCard = createCardElement(
                    event.event || 'Unnamed Event',
                    event.time_reference || 'No time reference available'
                );
                eventsList.appendChild(eventCard);
            });
        } else {
            eventsList.innerHTML = '<div class="alert alert-info">No timeline events found</div>';
        }
        
        // Display world rules
        const rulesList = document.getElementById('rulesList');
        rulesList.innerHTML = '';
        if (data.world_rules && data.world_rules.length > 0) {
            data.world_rules.forEach(rule => {
                const ruleCard = createCardElement(
                    rule.rule_name || 'Unnamed Rule',
                    rule.description || 'No description available'
                );
                rulesList.appendChild(ruleCard);
            });
        } else {
            rulesList.innerHTML = '<div class="alert alert-info">No world rules found</div>';
        }
        
        // Update character options for contradiction detection
        loadCharacterOptions();
        
        // Update element options for knowledge graph
        populateElementSelect();
    })
    .catch(error => {
        document.getElementById('extractElementsBtn').disabled = false;
        document.getElementById('extractElementsBtn').textContent = 'Extract Elements';
        alert(`Error: ${error}`);
    });
}

function createCardElement(title, bodyContent) {
    const card = document.createElement('div');
    card.className = 'card mb-3 data-card';
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    const cardTitle = document.createElement('h6');
    cardTitle.className = 'card-title';
    cardTitle.textContent = title;
    
    const cardText = document.createElement('div');
    cardText.className = 'card-text small';
    cardText.innerHTML = bodyContent;
    
    cardBody.appendChild(cardTitle);
    cardBody.appendChild(cardText);
    card.appendChild(cardBody);
    
    return card;
}

// Find Contradictions functionality
function loadCharacterOptions() {
    // This would fetch characters from the knowledge graph in a real implementation
    fetch('/api/knowledge_graph')
        .then(response => response.json())
        .then(data => {
            const characterSelect = document.getElementById('characterSelect');
            characterSelect.innerHTML = '<option value="">Select a character...</option>';
            
            // Simulate characters in knowledge graph
            if (data.element_types && data.element_types.character > 0) {
                // This is a placeholder - in a real implementation, we would use actual character data
                const dummyCharacters = [
                    { id: 'char_1', name: 'Character 1' },
                    { id: 'char_2', name: 'Character 2' },
                    { id: 'char_3', name: 'Character 3' }
                ];
                
                dummyCharacters.forEach(character => {
                    const option = document.createElement('option');
                    option.value = character.id;
                    option.textContent = character.name;
                    characterSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading character options:', error));
}

function findContradictions() {
    const contradictionType = document.getElementById('contradictionType').value;
    const character = document.getElementById('characterSelect').value;
    
    // Hide character select for world_rules only
    document.getElementById('characterSelectDiv').style.display = 
        (contradictionType === 'world_rules') ? 'none' : 'block';
    
    if (contradictionType === 'character' && !character) {
        alert('Please select a character');
        return;
    }
    
    document.getElementById('findContradictionsBtn').disabled = true;
    document.getElementById('findContradictionsBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
    
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query_type: 'detect_contradictions',
            content: character
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('findContradictionsBtn').disabled = false;
        document.getElementById('findContradictionsBtn').textContent = 'Find Contradictions';
        
        document.getElementById('noContradictionsMsg').style.display = 'none';
        document.getElementById('contradictionResults').style.display = 'block';
        
        // Display character contradictions
        const characterContradictions = document.getElementById('characterContradictions');
        characterContradictions.innerHTML = '';
        
        if (data.character_contradictions && data.character_contradictions.length > 0) {
            data.character_contradictions.forEach(contradiction => {
                const card = document.createElement('div');
                card.className = 'card contradiction-card mb-3';
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const description = document.createElement('p');
                description.textContent = contradiction.description;
                
                const resolution = document.createElement('div');
                resolution.className = 'mt-2';
                resolution.innerHTML = '<strong>Possible Resolutions:</strong>';
                
                const resolutionList = document.createElement('ul');
                contradiction.resolution_options.forEach(option => {
                    const item = document.createElement('li');
                    item.textContent = option;
                    resolutionList.appendChild(item);
                });
                
                resolution.appendChild(resolutionList);
                cardBody.appendChild(description);
                cardBody.appendChild(resolution);
                card.appendChild(cardBody);
                
                characterContradictions.appendChild(card);
            });
        } else {
            characterContradictions.innerHTML = '<div class="alert alert-info">No character timeline contradictions found</div>';
        }
        
        // Display rule contradictions
        const ruleContradictions = document.getElementById('ruleContradictions');
        ruleContradictions.innerHTML = '';
        
        if (data.rule_contradictions && data.rule_contradictions.length > 0) {
            data.rule_contradictions.forEach(contradiction => {
                const card = document.createElement('div');
                card.className = 'card contradiction-card mb-3';
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const description = document.createElement('p');
                description.textContent = contradiction.description;
                
                const resolution = document.createElement('div');
                resolution.className = 'mt-2';
                resolution.innerHTML = '<strong>Possible Resolutions:</strong>';
                
                const resolutionList = document.createElement('ul');
                contradiction.resolution_options.forEach(option => {
                    const item = document.createElement('li');
                    item.textContent = option;
                    resolutionList.appendChild(item);
                });
                
                resolution.appendChild(resolutionList);
                cardBody.appendChild(description);
                cardBody.appendChild(resolution);
                card.appendChild(cardBody);
                
                ruleContradictions.appendChild(card);
            });
        } else {
            ruleContradictions.innerHTML = '<div class="alert alert-info">No world rule contradictions found</div>';
        }
    })
    .catch(error => {
        document.getElementById('findContradictionsBtn').disabled = false;
        document.getElementById('findContradictionsBtn').textContent = 'Find Contradictions';
        alert(`Error: ${error}`);
    });
}

// Fact Check functionality
function checkFact() {
    const universe = document.getElementById('universeForFactCheck').value;
    const statement = document.getElementById('factCheckStatement').value;
    
    if (!universe || !statement) {
        alert('Please select a universe and enter a statement');
        return;
    }
    
    document.getElementById('checkFactBtn').disabled = true;
    document.getElementById('checkFactBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
    
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query_type: 'fact_check',
            content: statement,
            universe: universe === 'custom' ? document.getElementById('customUniverse').value : universe
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('checkFactBtn').disabled = false;
        document.getElementById('checkFactBtn').textContent = 'Check Statement';
        
        document.getElementById('noFactCheckMsg').style.display = 'none';
        document.getElementById('factCheckResults').style.display = 'block';
        
        // Update status badge
        const statusBadge = document.getElementById('statusBadge');
        statusBadge.textContent = data.status.toUpperCase();
        statusBadge.className = `status-badge status-${data.status.toLowerCase()}`;
        
        // Update confidence
        document.getElementById('confidenceDisplay').textContent = `Confidence: ${(data.confidence * 100).toFixed(0)}%`;
        
        // Update explanation
        document.getElementById('explanationText').textContent = data.explanation;
        
        // Mock related elements (would be real data in production)
        const relatedElements = document.getElementById('relatedElements');
        relatedElements.innerHTML = '';
        
        // Simulate related elements
        const mockElements = [
            { type: 'character', name: 'Related Character', confidence: 0.9 },
            { type: 'location', name: 'Related Location', confidence: 0.7 },
            { type: 'world_rule', name: 'Related Rule', confidence: 0.8 }
        ];
        
        mockElements.forEach(element => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary me-2 mb-2';
            
            let icon = '';
            switch(element.type) {
                case 'character': icon = '<i class="fas fa-user me-1"></i>'; break;
                case 'location': icon = '<i class="fas fa-map-marker-alt me-1"></i>'; break;
                case 'timeline_event': icon = '<i class="fas fa-calendar me-1"></i>'; break;
                case 'world_rule': icon = '<i class="fas fa-book me-1"></i>'; break;
            }
            
            badge.innerHTML = `${icon}${element.name} (${(element.confidence * 100).toFixed(0)}%)`;
            relatedElements.appendChild(badge);
        });
    })
    .catch(error => {
        document.getElementById('checkFactBtn').disabled = false;
        document.getElementById('checkFactBtn').textContent = 'Check Statement';
        alert(`Error: ${error}`);
    });
}

// Knowledge Graph functionality
function populateElementSelect() {
    fetch('/api/knowledge_graph')
        .then(response => response.json())
        .then(data => {
            const elementSelect = document.getElementById('elementSelect');
            elementSelect.innerHTML = '<option value="">Select an element...</option>';
            
            // Update graph statistics
            document.getElementById('nodeCount').textContent = data.node_count || 0;
            document.getElementById('edgeCount').textContent = data.edge_count || 0;
            document.getElementById('charCount').textContent = data.element_types?.character || 0;
            document.getElementById('locCount').textContent = data.element_types?.location || 0;
            document.getElementById('eventCount').textContent = data.element_types?.timeline_event || 0;
            document.getElementById('ruleCount').textContent = data.element_types?.world_rule || 0;
            
            // For demonstration, add mock elements
            if (data.node_count > 0) {
                const mockElements = [
                    { id: 'char_1', type: 'character', name: 'Character 1' },
                    { id: 'char_2', type: 'character', name: 'Character 2' },
                    { id: 'loc_1', type: 'location', name: 'Location 1' },
                    { id: 'event_1', type: 'timeline_event', name: 'Event 1' },
                    { id: 'rule_1', type: 'world_rule', name: 'Rule 1' }
                ];
                
                mockElements.forEach(element => {
                    const option = document.createElement('option');
                    option.value = element.id;
                    
                    let icon = '';
                    switch(element.type) {
                        case 'character': icon = '👤 '; break;
                        case 'location': icon = '📍 '; break;
                        case 'timeline_event': icon = '📅 '; break;
                        case 'world_rule': icon = '📜 '; break;
                    }
                    
                    option.textContent = `${icon}${element.name}`;
                    elementSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading elements:', error));
}

function loadKnowledgeGraphStats() {
    fetch('/api/knowledge_graph')
        .then(response => response.json())
        .then(data => {
            document.getElementById('nodeCount').textContent = data.node_count || 0;
            document.getElementById('edgeCount').textContent = data.edge_count || 0;
            document.getElementById('charCount').textContent = data.element_types?.character || 0;
            document.getElementById('locCount').textContent = data.element_types?.location || 0;
            document.getElementById('eventCount').textContent = data.element_types?.timeline_event || 0;
            document.getElementById('ruleCount').textContent = data.element_types?.world_rule || 0;
        })
        .catch(error => console.error('Error loading graph stats:', error));
}

function updateGraph() {
    const elementId = document.getElementById('elementSelect').value;
    const depth = document.getElementById('depthSlider').value;
    
    if (!elementId) {
        alert('Please select an element');
        return;
    }
    
    document.getElementById('updateGraphBtn').disabled = true;
    document.getElementById('updateGraphBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
    
    fetch(`/api/knowledge_graph?element_id=${elementId}&depth=${depth}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('updateGraphBtn').disabled = false;
            document.getElementById('updateGraphBtn').textContent = 'Update Graph';
            
            document.getElementById('noGraphDataMsg').style.display = 'none';
            
            // This is just a mock visualization
            // In a real implementation, you would use a library like D3.js or Cytoscape.js
            
            const graphDiv = document.getElementById('knowledgeGraph');
            graphDiv.innerHTML = `<div class="alert alert-success">
                <i class="fas fa-check-circle"></i> Graph loaded with ${data.nodes?.length || 0} nodes and ${data.edges?.length || 0} edges
                <p class="mt-3">In a real implementation, this would be an interactive visualization using D3.js or a similar library.</p>
            </div>`;
            
            // Show mock element details
            document.getElementById('elementDetails').style.display = 'block';
            document.getElementById('selectedElementName').textContent = `Selected: ${document.getElementById('elementSelect').options[document.getElementById('elementSelect').selectedIndex].text}`;
            
            const detailsDiv = document.getElementById('selectedElementDetails');
            detailsDiv.innerHTML = `
                <p><strong>ID:</strong> ${elementId}</p>
                <p><strong>Connections:</strong> ${data.edges?.length || 0}</p>
                <p><strong>Confidence:</strong> 85%</p>
                <p><strong>Sources:</strong> Primary Novel, Author Statements</p>
            `;
        })
        .catch(error => {
            document.getElementById('updateGraphBtn').disabled = false;
            document.getElementById('updateGraphBtn').textContent = 'Update Graph';
            alert(`Error: ${error}`);
        });
}

// Open Questions functionality
function findOpenQuestions() {
    const universeSelect = document.getElementById('universeForQuestions');
    const universe = universeSelect.value;
    
    if (!universe) {
        alert('Please select a universe');
        return;
    }
    
    const universeName = universe === 'custom' ? 
        document.getElementById('customUniverse').value : 
        universeSelect.options[universeSelect.selectedIndex].text;
    
    document.getElementById('findQuestionsBtn').disabled = true;
    document.getElementById('findQuestionsBtn').innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Analyzing...';
    
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query_type: 'open_questions',
            universe: universe === 'custom' ? document.getElementById('customUniverse').value : universe
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('findQuestionsBtn').disabled = false;
        document.getElementById('findQuestionsBtn').textContent = 'Find Open Questions';
        
        document.getElementById('noQuestionsMsg').style.display = 'none';
        document.getElementById('openQuestionsList').style.display = 'block';
        
        const questionsList = document.getElementById('openQuestionsList');
        questionsList.innerHTML = '';
        
        if (data.length > 0) {
            data.forEach(question => {
                const card = document.createElement('div');
                card.className = 'card mb-3';
                
                const cardHeader = document.createElement('div');
                cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
                
                const title = document.createElement('h6');
                title.className = 'mb-0';
                title.textContent = question.question;
                
                const badge = document.createElement('span');
                badge.className = `badge ${getSpeculationBadgeClass(question.speculation_potential)}`;
                badge.textContent = `Speculation: ${question.speculation_potential}`;
                
                cardHeader.appendChild(title);
                cardHeader.appendChild(badge);
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const impact = document.createElement('p');
                impact.innerHTML = `<strong>Narrative Impact:</strong> ${question.narrative_impact}`;
                
                const relatedElements = document.createElement('div');
                relatedElements.className = 'mt-2';
                relatedElements.innerHTML = '<strong>Related Elements:</strong> ';
                
                question.related_elements.forEach((element, index) => {
                    const elementBadge = document.createElement('span');
                    elementBadge.className = 'badge bg-secondary me-1';
                    elementBadge.textContent = element;
                    relatedElements.appendChild(elementBadge);
                });
                
                cardBody.appendChild(impact);
                cardBody.appendChild(relatedElements);
                
                card.appendChild(cardHeader);
                card.appendChild(cardBody);
                
                questionsList.appendChild(card);
            });
        } else {
            questionsList.innerHTML = '<div class="alert alert-info">No open questions found for this universe</div>';
        }
    })
    .catch(error => {
        document.getElementById('findQuestionsBtn').disabled = false;
        document.getElementById('findQuestionsBtn').textContent = 'Find Open Questions';
        alert(`Error: ${error}`);
    });
}

function getSpeculationBadgeClass(potential) {
    switch(potential.toLowerCase()) {
        case 'high': return 'bg-danger';
        case 'medium': return 'bg-warning text-dark';
        case 'low': return 'bg-info text-dark';
        default: return 'bg-secondary';
    }
}

// Search Datasets functionality
function searchDatasets() {
    const query = document.getElementById('datasetQuery').value;
    
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    document.getElementById('searchDatasetsBtn').disabled = true;
    document.getElementById('search