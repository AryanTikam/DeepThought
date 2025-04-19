let universeCounter = 0;

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  sidebar.classList.toggle('collapsed');
  mainContent.classList.toggle('expanded');
}

function addUniverse() {
  const universeName = prompt("Enter the name of the universe:", `🌌 Universe ${universeCounter + 1}`);
  
  if (!universeName) return; // Don't proceed if the user cancels or enters an empty name

  const universeList = document.getElementById('universe-list');
  const universeId = `universe-${universeCounter++}`;

  const universe = document.createElement('div');
  universe.className = 'universe';
  universe.setAttribute('draggable', 'true');
  universe.id = universeId;
  
  // Create an icon and a span for the universe name
  const icon = document.createElement('i');
  icon.className = 'fas fa-globe';
  const nameSpan = document.createElement('span');
  nameSpan.textContent = universeName;
  
  universe.appendChild(icon);
  universe.appendChild(nameSpan);
  
  universe.addEventListener('click', () => handleUniverseClick(universeId));

  const fileContainer = document.createElement('div');
  fileContainer.className = 'file-container';
  fileContainer.dataset.universeId = universeId;
  
  // Add dropzone for files
  const dropZone = document.createElement('div');
  dropZone.className = 'file-dropzone';
  dropZone.innerHTML = '<i class="fas fa-cloud-upload-alt"></i><p>Drop files here or click to upload</p>';
  dropZone.addEventListener('click', () => triggerFileUpload(universeId));
  setupDropZone(dropZone, universeId);
  
  fileContainer.appendChild(dropZone);

  universeList.appendChild(universe);
  universeList.appendChild(fileContainer);

  enableDragAndDrop();
  
  // Show animation for new universe
  setTimeout(() => {
    universe.classList.add('show');
  }, 10);
}

function setupDropZone(dropZone, universeId) {
  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('dragover');
  });
  
  dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('dragover');
  });
  
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('dragover');
    
    if (e.dataTransfer.files.length) {
      // Handle file upload
      handleFileUpload({ target: { files: e.dataTransfer.files } }, universeId);
    } else if (e.dataTransfer.getData('fileId')) {
      // Handle file dragged from another universe
      const fileId = e.dataTransfer.getData('fileId');
      const sourceUniverseId = e.dataTransfer.getData('sourceUniverseId');
      moveFileBetweenUniverses(fileId, sourceUniverseId, universeId);
    }
  });
}

function triggerFileUpload(universeId) {
  const fileInput = document.getElementById('file-upload');
  fileInput.setAttribute('data-target-universe', universeId);
  fileInput.click();
}

function moveFileBetweenUniverses(fileId, sourceUniverseId, targetUniverseId) {
  if (sourceUniverseId === targetUniverseId) return;
  
  const fileElement = document.getElementById(fileId);
  if (!fileElement) return;
  
  const targetContainer = document.querySelector(`[data-universe-id="${targetUniverseId}"]`);
  if (!targetContainer) return;
  
  // Clone the file item and add to target universe
  const newFileItem = fileElement.cloneNode(true);
  
  // Update the delete button event listener
  const deleteButton = newFileItem.querySelector('button');
  deleteButton.onclick = () => newFileItem.remove();
  
  // Add the file to the target universe
  targetContainer.appendChild(newFileItem);
  
  // Remove from source if it's a move operation
  fileElement.remove();
  
  // Show notification
  showNotification(`File moved to ${document.getElementById(targetUniverseId).querySelector('span').textContent}`);
}

function showNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.classList.add('show');
    
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 2000);
  }, 10);
}

function deleteUniverse() {
  const selected = document.querySelector('.universe.selected');
  if (selected) {
    const universeId = selected.id;
    const container = document.querySelector(`[data-universe-id="${universeId}"]`);
    
    // Add exit animation
    selected.classList.add('remove');
    if (container) container.classList.add('remove');
    
    // Remove after animation completes
    setTimeout(() => {
      selected.remove();
      if (container) container.remove();
      showNotification('Universe deleted');
    }, 300);
  }
}

function handleUniverseClick(id) {
  const allUniverses = document.querySelectorAll('.universe');
  allUniverses.forEach(u => u.classList.remove('selected'));

  const clicked = document.getElementById(id);
  clicked.classList.add('selected');
  
  // Toggle file container visibility
  const fileContainers = document.querySelectorAll('.file-container');
  fileContainers.forEach(container => {
    if (container.dataset.universeId === id) {
      container.classList.add('show');
    } else {
      container.classList.remove('show');
    }
  });
  
  const universeName = clicked.querySelector('span').textContent;
  document.getElementById('chat-output').innerHTML = `
    <div class="universe-info">
      <h3><i class="fas fa-globe-americas"></i> ${universeName}</h3>
      <p>Explore this universe or add files to begin analysis.</p>
    </div>
  `;
}

function enableDragAndDrop() {
  // Universe drag and drop
  const universes = document.querySelectorAll('.universe');
  let dragSrc = null;

  universes.forEach(universe => {
    universe.addEventListener('dragstart', function (e) {
      dragSrc = this;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('universeId', this.id);
      this.classList.add('dragging');
    });

    universe.addEventListener('dragend', function() {
      this.classList.remove('dragging');
    });

    universe.addEventListener('dragover', function (e) {
      e.preventDefault();
      this.classList.add('dragover');
      return false;
    });
    
    universe.addEventListener('dragleave', function (e) {
      this.classList.remove('dragover');
    });

    universe.addEventListener('drop', function (e) {
      e.stopPropagation();
      e.preventDefault();
      this.classList.remove('dragover');
      
      const draggedUniverseId = e.dataTransfer.getData('universeId');
      if (draggedUniverseId && dragSrc !== this) {
        const list = document.getElementById('universe-list');
        const draggedUniverse = document.getElementById(draggedUniverseId);
        const filesA = document.querySelector(`[data-universe-id="${draggedUniverseId}"]`);
        const filesB = document.querySelector(`[data-universe-id="${this.id}"]`);

        list.insertBefore(draggedUniverse, this);
        list.insertBefore(filesA, filesB);
        
        showNotification('Universe order updated');
      }
      return false;
    });
  });
}

function sendMessage() {
  const input = document.getElementById('user-input');
  const message = input.value.trim();
  if (!message) return;
  
  const chatOutput = document.getElementById('chat-output');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message user-message';
  msgDiv.innerHTML = `
    <div class="message-content">
      <i class="fas fa-user"></i>
      <span>${message}</span>
    </div>
  `;
  
  chatOutput.appendChild(msgDiv);
  input.value = '';
  
  // Scroll to bottom
  chatOutput.scrollTop = chatOutput.scrollHeight;
  
  // Simulate response after a short delay
  setTimeout(() => {
    const responseDiv = document.createElement('div');
    responseDiv.className = 'message assistant-message';
    responseDiv.innerHTML = `
      <div class="message-content">
        <i class="fas fa-robot"></i>
        <span>I'm analyzing your query about "${message.substring(0, 30)}${message.length > 30 ? '...' : ''}"</span>
      </div>
    `;
    
    chatOutput.appendChild(responseDiv);
    chatOutput.scrollTop = chatOutput.scrollHeight;
  }, 800);
}

function showKnowledgeGraph() {
  document.getElementById('chat-output').innerHTML = `
    <div class="visualization-container">
      <div class="visualization-header">
        <i class="fas fa-brain"></i>
        <h3>Knowledge Graph</h3>
      </div>
      <div class="visualization-content">
        <div class="graph-placeholder">
          <i class="fas fa-project-diagram"></i>
          <p>Interactive knowledge graph will be displayed here.</p>
          <p class="small">Upload files to universes to visualize connections.</p>
        </div>
      </div>
    </div>
  `;
}

function showContradictionReport() {
  document.getElementById('chat-output').innerHTML = `
    <div class="visualization-container">
      <div class="visualization-header">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Contradiction Report</h3>
      </div>
      <div class="visualization-content">
        <div class="report-placeholder">
          <i class="fas fa-file-alt"></i>
          <p>Contradiction analysis will appear here.</p>
          <p class="small">Upload multiple documents to detect conflicts and inconsistencies.</p>
        </div>
      </div>
    </div>
  `;
}

// Handle file uploads and processing
document.getElementById('file-upload').addEventListener('change', function(event) {
  const targetUniverseId = this.getAttribute('data-target-universe');
  handleFileUpload(event, targetUniverseId);
});

function handleFileUpload(event, specifiedUniverseId) {
  const fileList = event.target.files;
  if (!fileList.length) return;
  
  // Get universe container - either specified or selected
  let universeId = specifiedUniverseId;
  if (!universeId) {
    const selectedUniverse = document.querySelector('.universe.selected');
    if (!selectedUniverse) {
      alert("Please select a universe to upload files to.");
      return;
    }
    universeId = selectedUniverse.id;
  }
  
  const fileContainer = document.querySelector(`[data-universe-id="${universeId}"]`);
  if (!fileContainer) return;

  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];
    const fileId = `file-${Date.now()}-${i}`;
    
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = fileId;
    fileItem.setAttribute('draggable', true);
    
    // Determine file icon based on extension
    let fileIcon = 'fa-file';
    const extension = file.name.split('.').pop().toLowerCase();
    if (['pdf'].includes(extension)) fileIcon = 'fa-file-pdf';
    else if (['doc', 'docx'].includes(extension)) fileIcon = 'fa-file-word';
    else if (['txt', 'md'].includes(extension)) fileIcon = 'fa-file-alt';
    else if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) fileIcon = 'fa-file-image';
    
    fileItem.innerHTML = `
      <div class="file-info">
        <i class="fas ${fileIcon}"></i>
        <span>${file.name}</span>
      </div>
      <div class="file-actions">
        <button class="btn-delete-file" title="Delete file">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    `;
    
    // Setup event listeners for file dragging
    fileItem.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('fileId', fileId);
      e.dataTransfer.setData('sourceUniverseId', universeId);
      e.dataTransfer.effectAllowed = 'move';
      fileItem.classList.add('dragging');
    });
    
    fileItem.addEventListener('dragend', () => {
      fileItem.classList.remove('dragging');
    });
    
    // Add event listener to delete button
    const deleteButton = fileItem.querySelector('.btn-delete-file');
    deleteButton.addEventListener('click', () => {
      fileItem.classList.add('remove');
      setTimeout(() => {
        fileItem.remove();
        showNotification(`${file.name} deleted`);
      }, 300);
    });
    
    // Insert file item before the dropzone
    const dropZone = fileContainer.querySelector('.file-dropzone');
    fileContainer.insertBefore(fileItem, dropZone);
    
    // Add show animation
    setTimeout(() => {
      fileItem.classList.add('show');
    }, 10);
  }
  
  showNotification(`${fileList.length} file${fileList.length > 1 ? 's' : ''} uploaded`);
}

// Initialize the app
window.addEventListener('DOMContentLoaded', () => {
  // Create a default universe
  addUniverse();
  
  // Add enter key support for chat
  document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });
});