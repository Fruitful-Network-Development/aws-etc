async function loadUserData() {
  const response = await fetch('user_data.json');
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

document.addEventListener('DOMContentLoaded', async () => {
  try {
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

    // blocks -> boxes in grid
    const anthGrid = document.querySelector("[data-slot='dossier.anthology.blocks']");
    if (anthGrid && Array.isArray(anthology.blocks)) {
      anthGrid.innerHTML = "";

      anthology.blocks.forEach(block => {
        if (typeof block !== 'object' || block === null) {
          return; // skip any non-object placeholders
        }

        const box = document.createElement('div');
        box.className = 'anthology-box';

        // clickable wrapper if there is a target
        let inner = box;
        if (block.target) {
          const link = document.createElement('a');
          link.href = block.target;
          // open external URLs in new tab, PDFs/local paths can be same tab
          if (block.kind === 'url' && /^https?:\/\//i.test(block.target)) {
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
          }
          link.className = 'anthology-link';
          box.appendChild(link);
          inner = link;
        }

        // Thumbnail (if exists) or text placeholder
        if (block.thumbnail) {
          const img = document.createElement('img');
          img.className = 'anthology-thumb';
          img.src = block.thumbnail;          // e.g. "assets/anthology/abc123.png"
          img.alt = block.title || block.id || '';
          inner.appendChild(img);

          // Optional caption under the image
          const caption = document.createElement('div');
          caption.className = 'anthology-caption';
          caption.textContent = block.title || block.id || '';
          box.appendChild(caption);
        } else {
          // Text-only placeholder
          const span = document.createElement('span');
          span.className = 'anthology-placeholder';
          span.textContent = block.title || block.id || '';
          inner.appendChild(span);
        }

        anthGrid.appendChild(box);
      });
    }

  } catch (err) {
    console.error('Error loading user data:', err);
  }
});
