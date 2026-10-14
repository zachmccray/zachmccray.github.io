// Firebase config
const firebaseConfig = {
    apiKey: "AIzaSyCAcgsiEGMCuEUOPQKNTJwhDASqCZqPyTs",
    authDomain: "website-blog-e4350.firebaseapp.com",
    databaseURL: "https://website-blog-e4350-default-rtdb.firebaseio.com",
    projectId: "website-blog-e4350",
    storageBucket: "website-blog-e4350.firebaseapp.com",
    messagingSenderId: "602771727086",
    appId: "1:602771727086:web:b42de71f386f3e9ecfc9ff",
    measurementId: "G-CVKK0PQ7Z1"
  };
  
// These globals and record paths retain the existing Firebase integration.
let db = null;
let userId = null;

function whenReady(callback) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", callback, { once: true });
  } else {
    callback();
  }
}

function feedback(id, message) {
  const button = Array.from(document.querySelectorAll('.share-button'))
    .find(button => button.dataset.id === id);
  const status = button?.closest('.travel-card')?.querySelector('.travel-feedback');
  if (status) status.textContent = message;
}

function reportFirebaseError(stage, error) {
  // Report the SDK category, never user IDs, snapshots or authentication tokens.
  console.warn('Travel Firebase operation unavailable', { stage, code: error?.code || 'unknown' });
}

function likesUnavailable(message = 'Likes are currently unavailable.') {
  document.querySelectorAll('.like-button').forEach(button => {
    button.disabled = true;
    button.setAttribute('aria-busy', 'false');
    button.title = 'Likes are currently unavailable';
    feedback(button.dataset.id, message);
  });
}

if (typeof firebase !== "undefined" && typeof firebase.initializeApp === "function"
    && typeof firebase.database === "function" && typeof firebase.auth === "function") {
  firebase.initializeApp(firebaseConfig);
  db = firebase.database();
  firebase.auth().signInAnonymously()
    .then(userCredential => {
      userId = userCredential.user.uid;
      // Cached authentication can resolve before the head finishes parsing.
      whenReady(() => {
        initLikeButtons();
        initShareCounts();
      });
    })
    .catch(error => {
      reportFirebaseError('authentication', error);
      whenReady(() => likesUnavailable('Likes are unavailable because sign-in failed.'));
    });
} else {
  // Keep ordinary navigation and clipboard/native sharing usable if the CDN fails.
  whenReady(likesUnavailable);
}

function initLikeButtons() {
  document.querySelectorAll('.like-button').forEach(button => {
    const id = button.getAttribute('data-id');
    if (!id) return;
    const countSpan = button.parentElement.querySelector('.like-count');
    // Only count and this user's marker are read. The owner-supplied rules
    // deny parent writes and do not enforce safe atomic counter transitions.
    // Keep mutations paused until an approved rules/backend solution is tested.
    const userLikeRef = db.ref('likes/' + id + '/users/' + userId);
    const countRef = db.ref('likes/' + id + '/count');
    button.disabled = true;
    button.setAttribute('aria-busy', 'false');
    button.title = 'Likes paused while secure updates are verified';
    feedback(id, 'Likes are paused while secure updates are verified.');
    countRef.on('value', snapshot => {
      const value = snapshot.val();
      if (value != null && (!Number.isSafeInteger(value) || value < 0)) {
        countSpan.textContent = '—';
        countSpan.setAttribute('aria-label', 'Like count unavailable');
        feedback(id, 'The stored like count is invalid. No update was attempted.');
        return;
      }
      countSpan.textContent = value ?? 0;
      countSpan.setAttribute('aria-label', countSpan.textContent + ' likes');
    }, error => {
      reportFirebaseError('like-count-read', error);
      feedback(id, 'The like count is currently unavailable. No update was attempted.');
    });
    userLikeRef.on('value', snapshot => {
      button.classList.toggle('liked', snapshot.exists());
      button.setAttribute('aria-pressed', String(snapshot.exists()));
    }, error => {
      reportFirebaseError('own-like-read', error);
      feedback(id, 'Your like state is currently unavailable. No update was attempted.');
    });
  });
}

// Retain the native-share/clipboard branches, URL arguments and counter semantics.
async function sharePost(url, id = null) {
  const button = Array.from(document.querySelectorAll('.share-button'))
    .find(button => button.dataset.id === id);
  if (button?.disabled) return;
  if (button) button.disabled = true;
  try {
    if (navigator.share) {
      await navigator.share({ title: button?.closest('.travel-card')?.querySelector('.travel-card-title')?.textContent.trim() || document.title, text: 'Check out this post!', url });
      feedback(id, 'Shared.');
    } else if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url);
      feedback(id, 'Link copied to clipboard!');
    } else {
      feedback(id, 'Sharing is unavailable. Copy the article link instead.');
      return;
    }
    // Counter delivery must not hold a completed native share/clipboard action open.
    if (id) void logShareToFirebase(id);
  } catch (error) {
    feedback(id, error.name === 'AbortError' ? 'Sharing canceled.' : 'Could not share the link. Please try again.');
  } finally {
    if (button) button.disabled = false;
  }
}

async function logShareToFirebase(id) {
  if (!userId || !db) return;
  try {
    // One completion still counts once, including repeated shares by one user.
    // Atomic multi-path update needs no read access to other users' records.
    await db.ref('shares/' + id).update({
      ['users/' + userId]: {
        shared: true,
        timestamp: firebase.database.ServerValue.TIMESTAMP
      },
      count: firebase.database.ServerValue.increment(1)
    });
  } catch (_) {
    feedback(id, 'Link shared; the share count update could not be confirmed.');
  }
}

function initShareCounts() {
  document.querySelectorAll('.share-button').forEach(button => {
    const id = button.getAttribute('data-id');
    if (!id) return;
    const countSpan = button.parentElement.querySelector('.share-count');
    db.ref('shares/' + id + '/count').on('value', snapshot => {
      countSpan.textContent = snapshot.val() || 0;
      countSpan.setAttribute('aria-label', countSpan.textContent + ' shares');
    }, () => feedback(id, 'The share count is currently unavailable.'));
  });
}
