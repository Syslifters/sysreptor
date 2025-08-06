const PLUGIN_ID = 'ba67f081-bd60-426c-9830-90e71fbce844';


function getProjectIdFromUrl() {
  const match = window.location.pathname.match(/\/projects\/([^\/]+)\//);
  return match ? match[1] : null;
}

function addMarkdownExportButton() {
  const publishActionsDiv = document.getElementById('publish-actions-download');
  if (!publishActionsDiv) {
    return false;
  }

  // Check if button already exists to avoid duplicates
  const existingButton = publishActionsDiv.querySelector('#plugin-markdownexport-button');
  if (existingButton) {
    return true;
  }

  const projectId = getProjectIdFromUrl();
  if (!projectId) {
    return false;
  }

  // Create the markdown export button
  const button = document.createElement('a');
  button.id = 'plugin-markdownexport-button';
  button.href = `/api/plugins/${PLUGIN_ID}/api/projects/${projectId}/markdownexport/`;
  button.target = '_blank';
  button.className = 'v-btn bg-primary-bg v-btn--density-default v-btn--size-default v-btn--variant-flat mr-1 mb-1';
  button.innerHTML = `
    <span class="v-btn__overlay"></span>
    <span class="v-btn__underlay"></span>
    <span class="v-btn__prepend">
      <i class="v-icon v-icon--size-default mdi mdi-language-markdown"></i>
    </span>
    <span class="v-btn__content">Markdown Export</span>
  `;
  publishActionsDiv.appendChild(button);

  return true;
}

export default function () {
  // Set up MutationObserver to watch for DOM changes
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        // Check if the publish-actions-download div was added
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node;

            // Check if the added node is the target div or contains it
            if (element.id === 'publish-actions-download') {
              addMarkdownExportButton();
            } else if (element.querySelector && element.querySelector('#publish-actions-download')) {
              addMarkdownExportButton();
            }
          }
        });
      }
    });
  });

  // Start observing the document for changes
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}
