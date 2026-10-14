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
    button.setAttribute('aria-busy', 'false');
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

// A fixed desired state makes transaction retries idempotent, including an
// acknowledged-late write retried by the visitor. Existing fields stay intact.
function updateLikeRecord(current, uid, liked) {
  if (current != null && (typeof current !== 'object' || Array.isArray(current))) return undefined;
  const record = current || {};
  if (record.users != null && (typeof record.users !== 'object' || Array.isArray(record.users))) return undefined;
  const users = { ...(record.users || {}) };
  const wasLiked = users[uid] != null;
  const count = record.count == null ? 0 : record.count;
  if (!Number.isSafeInteger(count) || count < 0) return undefined;
  // A legacy split write can leave a marker without its count contribution.
  // Abort known inconsistent states rather than taking another user's like.
  if (count < Object.values(users).filter(value => value != null).length) return undefined;
  if (wasLiked === liked) return record;
  if (liked && count === Number.MAX_SAFE_INTEGER) return undefined;
  if (liked) users[uid] = { liked: true, timestamp: firebase.database.ServerValue.TIMESTAMP };
  else delete users[uid];
  return { ...record, users, count: liked ? count + 1 : Math.max(count - 1, 0) };
}

function initLikeButtons() {
  document.querySelectorAll('.like-button').forEach(button => {
    const id = button.getAttribute('data-id');
    if (!id) return;
    const countSpan = button.parentElement.querySelector('.like-count');
    const recordRef = db.ref('likes/' + id);
    const userLikeRef = recordRef.child('users/' + userId);
    const countRef = recordRef.child('count');
    let pendingLike = null;
    let saving = false;
    const setState = liked => {
      button.classList.toggle('liked', liked);
      button.setAttribute('aria-pressed', String(liked));
      button.title = liked ? 'You already liked this' : 'Click to like this';
    };
    countRef.on('value', snapshot => {
      countSpan.textContent = snapshot.val() || 0;
      countSpan.setAttribute('aria-label', countSpan.textContent + ' likes');
    }, () => feedback(id, 'The like count is currently unavailable.'));
    userLikeRef.on('value', snapshot => {
      if (saving) return;
      setState(snapshot.exists());
      button.disabled = false;
      button.setAttribute('aria-busy', 'false');
    }, () => {
      button.disabled = true;
      button.setAttribute('aria-busy', 'false');
      button.title = 'Likes are currently unavailable';
      feedback(id, 'Likes are currently unavailable.');
    });

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      // Keep this intent after an uncertain failure instead of flipping it on retry.
      if (pendingLike === null) pendingLike = button.getAttribute('aria-pressed') !== 'true';
      const liked = pendingLike;
      saving = true;
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      feedback(id, 'Saving your like…');
      try {
        const result = await recordRef.transaction(
          current => updateLikeRecord(current, userId, liked), undefined, false
        );
        if (!result.committed) throw new Error('Like was not committed');
        setState(result.snapshot.child('users/' + userId).exists());
        feedback(id, pendingLike ? 'Liked.' : 'Like removed.');
        pendingLike = null;
      } catch (_) {
        feedback(id, 'Could not confirm the like update. Retry to finish the same action.');
      } finally {
        saving = false;
        button.disabled = false;
        button.setAttribute('aria-busy', 'false');
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
