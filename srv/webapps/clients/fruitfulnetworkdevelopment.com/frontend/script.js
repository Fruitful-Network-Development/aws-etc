// /srv/webapps/clients/fruitfulnetworkdevelopment.com/frontend/script.js

async function loadUserData() {
  const USER_DATA_FILENAME = 'msn_32357767435.json';

  // Check for ?external=client-slug in the URL
  const params = new URLSearchParams(window.location.search);
  let dataUrl = `/${USER_DATA_FILENAME}`;  // default local path

  const externalSlug = params.get('external');
  if (externalSlug) {
    // If present, point to our proxy route; the slug may include dots
    dataUrl = `/proxy/${externalSlug}/${USER_DATA_FILENAME}`;
  }

  // Fetch the chosen JSON URL
  const response = await fetch(dataUrl);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

function setText(selector, value) {
  const el = document.querySelector(selector);
  if (el && value != null) {
    el.textContent = value;
  }
}

function setImgSrc(selector, value) {
  const el = document.querySelector(selector);
  if (el && value) {
    el.src = value;
  }
}

/* ---------------- ANTHOLOGY OVERLAY STATE ---------------- */

let anthologyBlocks = [];
let currentAnthologyIndex = -1;

let overlayEls = {
  overlay: null,
  title: null,
  description: null,
  urlText: null,
  kind: null,
  targetLabel: null,
  canvas: null,
  closeBtn: null,
  prevBtn: null,
  nextBtn: null
};

function initOverlayElements() {
  overlayEls.overlay = document.getElementById('anthology-overlay');
  if (!overlayEls.overlay) return;

  overlayEls.title = document.getElementById('anthology-overlay-title');
  overlayEls.description = document.getElementById('anthology-overlay-description');
  overlayEls.urlText = document.getElementById('anthology-overlay-url');
  overlayEls.kind = document.getElementById('anthology-overlay-kind');
  overlayEls.targetLabel = document.getElementById('anthology-overlay-target-label');
  overlayEls.canvas = document.getElementById('anthology-overlay-canvas');
  overlayEls.closeBtn = document.getElementById('anthology-overlay-close');
  overlayEls.prevBtn = document.getElementById('anthology-overlay-prev');
  overlayEls.nextBtn = document.getElementById('anthology-overlay-next');

  // Close button
  if (overlayEls.closeBtn) {
    overlayEls.closeBtn.addEventListener('click', closeAnthologyOverlay);
  }

  // Clicking the dark background closes overlay
  overlayEls.overlay.addEventListener('click', (evt) => {
    if (evt.target === overlayEls.overlay) {
      closeAnthologyOverlay();
    }
  });

  // Keyboard controls
  document.addEventListener('keydown', (evt) => {
    if (!overlayEls.overlay || overlayEls.overlay.classList.contains('is-hidden')) {
      return;
    }
    if (evt.key === 'Escape') {
      closeAnthologyOverlay();
    } else if (evt.key === 'ArrowRight') {
      changeAnthologyOverlay(1);
    } else if (evt.key === 'ArrowLeft') {
      changeAnthologyOverlay(-1);
    }
  });

  // Prev/next buttons
  if (overlayEls.prevBtn) {
    overlayEls.prevBtn.addEventListener('click', () => changeAnthologyOverlay(-1));
  }
  if (overlayEls.nextBtn) {
    overlayEls.nextBtn.addEventListener('click', () => changeAnthologyOverlay(1));
  }
}

function openAnthologyOverlay(index) {
  if (!overlayEls.overlay || !anthologyBlocks.length) return;

  currentAnthologyIndex = index;
  updateAnthologyOverlay();

  overlayEls.overlay.classList.remove('is-hidden');
  document.body.classList.add('overlay-open');
}

function closeAnthologyOverlay() {
  if (!overlayEls.overlay) return;
  overlayEls.overlay.classList.add('is-hidden');
  document.body.classList.remove('overlay-open');
}

function changeAnthologyOverlay(delta) {
  if (!anthologyBlocks.length) return;
  currentAnthologyIndex =
    (currentAnthologyIndex + delta + anthologyBlocks.length) % anthologyBlocks.length;
  updateAnthologyOverlay();
}

function updateAnthologyOverlay() {
  const block = anthologyBlocks[currentAnthologyIndex];
  if (!block || !overlayEls.overlay) return;

  if (overlayEls.title) {
    overlayEls.title.textContent = block.title || block.id || 'Anthology item';
  }

  if (overlayEls.description) {
    // placeholder for future "description" field in JSON
    if (block.description) {
      overlayEls.description.textContent = block.description;
    } else {
      overlayEls.description.textContent =
        'More information about this entry will go here as the data model evolves.';
    }
  }

  const targetText = block.target || 'No link configured yet';

  if (overlayEls.urlText) {
    overlayEls.urlText.textContent = targetText;
  }
  if (overlayEls.kind) {
    overlayEls.kind.textContent = block.kind || '—';
  }
  if (overlayEls.targetLabel) {
    overlayEls.targetLabel.textContent = targetText;
  }

  if (overlayEls.canvas) {
    if (block.thumbnail) {
      overlayEls.canvas.style.backgroundImage = `url(${block.thumbnail})`;
    } else {
      overlayEls.canvas.style.backgroundImage = 'none';
    }
  }
}

/* ---------------- MAIN DATA LOADING & BINDING ---------------- */

document.addEventListener('DOMContentLoaded', async () => {
  try {
    initOverlayElements();

    const data = await loadUserData();
    const mss = data.MSS || {};

    const compendium = mss.compendium || {};
    const profile = compendium.profile || {};

    const dossier = mss.dossier || {};
    const oeuvre = dossier.oeuvre || {};
    const anthology = dossier.anthology || {};

    /* ---------------- PROFILE / COMPENDIUM ---------------- */

    // name in meta-bar and profile card
    setText("[data-slot='compendium.profile.name']", profile.name);

    // avatar + micro icon
    setImgSrc("[data-slot='compendium.profile.avatar']", profile.avatar);
    setImgSrc("[data-slot='compendium.profile.micro_icon']", profile.micro_icon);

    // handle line (e.g. "dylcmonty • he/him")
    setText("[data-slot='compendium.profile.handleLine']", profile.handleLine);

    // handle @link, location, linkedin
    setText("[data-slot='compendium.profile.displayHandle']", profile.displayHandle);
    setText("[data-slot='compendium.profile.location']", profile.location);
    setText("[data-slot='compendium.profile.linkedin']", profile.linkedin);

    // compendium title (top of box)
    setText("[data-slot='compendium.title']", compendium.title);

    // organizations list
    const orgList = document.querySelector("[data-slot='compendium.organizations']");
    if (orgList && Array.isArray(compendium.organizations)) {
      orgList.innerHTML = "";
      compendium.organizations.forEach(org => {
        const li = document.createElement('li');
        li.textContent = org;
        orgList.appendChild(li);
      });
    }

    /* ---------------- DOSSIER / OEUVRE ---------------- */

    setText("[data-slot='dossier.oeuvre.title']", oeuvre.title);

    const oeuvreBody = document.querySelector("[data-slot='dossier.oeuvre.paragraphs']");
    if (oeuvreBody && Array.isArray(oeuvre.paragraphs)) {
      oeuvreBody.innerHTML = "";
      oeuvre.paragraphs.forEach(p => {
        const para = document.createElement('p');
        para.textContent = p;
        oeuvreBody.appendChild(para);
      });
    }

    /* ---------------- DOSSIER / ANTHOLOGY ---------------- */

    setText("[data-slot='dossier.anthology.title']", anthology.title);

    const anthGrid = document.querySelector("[data-slot='dossier.anthology.blocks']");
    if (anthGrid && Array.isArray(anthology.blocks)) {
      anthGrid.innerHTML = "";
      anthologyBlocks = [];

      anthology.blocks.forEach((block) => {
        if (typeof block !== 'object' || block === null) {
          return; // skip any non-object placeholders
        }

        const index = anthologyBlocks.length;
        anthologyBlocks.push(block);

        const box = document.createElement('div');
        box.className = 'anthology-box';

        // default clickable element is the box itself
        let clickableEl = box;

        // if there is a target, keep href semantics but intercept to open overlay
        if (block.target) {
          const link = document.createElement('a');
          link.href = block.target;
          link.className = 'anthology-link';

          link.addEventListener('click', (evt) => {
            evt.preventDefault(); // do not navigate away
            openAnthologyOverlay(index);
          });

          box.appendChild(link);
          clickableEl = link;
        } else {
          // no target: click on box itself opens overlay
          box.addEventListener('click', () => openAnthologyOverlay(index));
        }

        // Thumbnail (if exists) or text placeholder
        if (block.thumbnail) {
          const img = document.createElement('img');
          img.src = block.thumbnail;
          img.alt = block.title || block.id || '';
          clickableEl.appendChild(img);
        } else {
          const label = document.createElement('div');
          label.className = 'anthology-placeholder';
          label.textContent = block.title || block.id || '';
          clickableEl.appendChild(label);
        }

        anthGrid.appendChild(box);
      });
    }

  } catch (err) {
    console.error('Error loading user data:', err);
  }
});
