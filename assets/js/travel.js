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

function likesUnavailable() {
  document.querySelectorAll('.like-button').forEach(button => {
    button.disabled = true;
    button.title = 'Likes are currently unavailable';
    feedback(button.dataset.id, 'Likes are currently unavailable.');
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
    .catch(() => whenReady(likesUnavailable));
} else {
  // Keep ordinary navigation and clipboard/native sharing usable if the CDN fails.
  whenReady(likesUnavailable);
}

function initLikeButtons() {
  document.querySelectorAll('.like-button').forEach(button => {
    const id = button.getAttribute('data-id');
    if (!id) return;
    const countSpan = button.parentElement.querySelector('.like-count');
    const userLikeRef = db.ref('likes/' + id + '/users/' + userId);
    const countRef = db.ref('likes/' + id + '/count');
    const setState = liked => {
      button.classList.toggle('liked', liked);
      button.setAttribute('aria-pressed', String(liked));
      button.title = liked ? 'You already liked this' : 'Click to like this';
    };
    countRef.on('value', snapshot => {
      countSpan.textContent = snapshot.val() || 0;
      countSpan.setAttribute('aria-label', countSpan.textContent + ' likes');
    }, () => feedback(id, 'The like count is currently unavailable.'));
    userLikeRef.once('value').then(snapshot => {
      setState(snapshot.exists());
      button.disabled = false;
    }).catch(() => feedback(id, 'Likes are currently unavailable.'));

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      button.disabled = true;
      try {
        const snapshot = await userLikeRef.once('value');
        const liked = !snapshot.exists();
        if (liked) {
          await userLikeRef.set({
            liked: true,
            timestamp: firebase.database.ServerValue.TIMESTAMP
          });
        } else {
          await userLikeRef.remove();
        }
        setState(liked);
        await countRef.transaction(current => liked
          ? (current || 0) + 1 : Math.max((current || 1) - 1, 0));
        feedback(id, liked ? 'Liked.' : 'Like removed.');
      } catch (_) {
        feedback(id, 'Could not update the like. Please try again.');
      } finally {
        button.disabled = false;
      }
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
      await navigator.share({ title: document.title, text: 'Check out this post!', url });
      feedback(id, 'Shared.');
    } else if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url);
      feedback(id, 'Link copied to clipboard!');
    } else {
      feedback(id, 'Sharing is unavailable. Copy the article link instead.');
      return;
    }
    if (id) await logShareToFirebase(id);
  } catch (error) {
    feedback(id, error.name === 'AbortError' ? 'Sharing canceled.' : 'Could not share the link. Please try again.');
  } finally {
    if (button) button.disabled = false;
  }
}

async function logShareToFirebase(id) {
  if (!userId || !db) return;
  try {
    await db.ref('shares/' + id + '/users/' + userId).set({
      shared: true,
      timestamp: firebase.database.ServerValue.TIMESTAMP
    });
    await db.ref('shares/' + id + '/count').transaction(current => (current || 0) + 1);
  } catch (_) {
    feedback(id, 'Link shared; the share count could not be updated.');
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
