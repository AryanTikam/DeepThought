let universeCounter = 0;

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('collapsed');
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
  universe.textContent = universeName;
  universe.addEventListener('click', () => handleUniverseClick(universeId));

  const fileContainer = document.createElement('div');
  fileContainer.className = 'file-container';
  fileContainer.dataset.universeId = universeId;

  universeList.appendChild(universe);
  universeList.appendChild(fileContainer);

  enableDragAndDrop();
}

function deleteUniverse() {
  const selected = document.querySelector('.universe.selected');
  if (selected) {
    const universeId = selected.id;
    const container = document.querySelector(`[data-universe-id="${universeId}"]`);
    selected.remove();
    if (container) container.remove();
  }
}

function handleUniverseClick(id) {
  const allUniverses = document.querySelectorAll('.universe');
  allUniverses.forEach(u => u.classList.remove('selected'));

  const clicked = document.getElementById(id);
  clicked.classList.add('selected');
  document.getElementById('chat-output').innerHTML = `<p>📄 Loading report for ${clicked.textContent}...</p>`;

  // Placeholder for files inside this universe (e.g., list text files)
  const fileContainer = document.querySelector(`[data-universe-id="${id}"]`);
  fileContainer.innerHTML = `<p>📝 Files will appear here...</p>`;  // Placeholder message
}

function enableDragAndDrop() {
  const items = document.querySelectorAll('.universe');
  let dragSrc = null;

  items.forEach(item => {
    item.addEventListener('dragstart', function (e) {
      dragSrc = this;
      e.dataTransfer.effectAllowed = 'move';
    });

    item.addEventListener('dragover', function (e) {
      e.preventDefault();
      return false;
    });

    item.addEventListener('drop', function (e) {
      e.stopPropagation();
      if (dragSrc !== this) {
        const list = document.getElementById('universe-list');
        const filesA = document.querySelector(`[data-universe-id="${dragSrc.id}"]`);
        const filesB = document.querySelector(`[data-universe-id="${this.id}"]`);

        list.insertBefore(dragSrc, this);
        list.insertBefore(filesA, filesB);
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
  msgDiv.textContent = `🧑‍💻 ${message}`;
  chatOutput.appendChild(msgDiv);
  input.value = '';
}

function showKnowledgeGraph() {
  document.getElementById('chat-output').innerHTML = `<p>📈 Displaying knowledge graph (Mockup)</p>`;
}

function showContradictionReport() {
  document.getElementById('chat-output').innerHTML = `<p>⚠️ Displaying contradictions (Mockup)</p>`;
}

// Handle file uploads and processing (this will need more backend integration for full functionality)
document.getElementById('file-upload').addEventListener('change', handleFileUpload);

function handleFileUpload(event) {
  const fileList = event.target.files;
  const fileContainer = document.querySelector(`[data-universe-id="${document.querySelector('.universe.selected')?.id}"]`);

  if (!fileContainer) {
    alert("Please select a universe to upload files to.");
    return;
  }

  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.textContent = file.name;

    // Add event listeners for file actions (like delete)
    const deleteButton = document.createElement('button');
    deleteButton.textContent = "Delete";
    deleteButton.onclick = () => fileItem.remove();

    fileItem.appendChild(deleteButton);
    fileContainer.appendChild(fileItem);
  }
}
