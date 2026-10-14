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
      whenReady(() => likesUnavailable('Likes are temporarily unavailable. Please try again later.'));
    });
} else {
  // Keep ordinary navigation and clipboard/native sharing usable if the CDN fails.
  whenReady(likesUnavailable);
}

// Private action IDs are technical retry receipts, not personal visitor details.
function counterActionId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), byte => byte.toString(16).padStart(2, '0')).join('');
}

function validLikeReceipt(value) {
  return value && Number.isSafeInteger(value.revision) && value.revision >= 0
    && typeof value.liked === 'boolean' && typeof value.actionId === 'string'
    && Object.keys(value).sort().join(',') === 'actionId,liked,revision'
    && (value.revision === 0 ? value.actionId === 'initial' : /^[a-f0-9]{32}$/.test(value.actionId));
}

// SDK get()/value events can use an optimistic/offline cache. A rules-validated
// no-op write is the acknowledgement barrier; a cached snapshot alone isn't proof.
async function confirmedLikeState(database, uid, id) {
  const ref = database.ref('likes/' + id);
  let lastError;
  for (let attempt = 0; attempt < 5; attempt++) {
    const snapshot = await ref.child('receipts/' + uid).get();
    let state = snapshot.val();
    if (state == null) {
      state = { revision: 0, liked: (await ref.child('users/' + uid).get()).exists(), actionId: 'initial' };
    }
    if (!validLikeReceipt(state)) throw Object.assign(new Error('Invalid like receipt'), { code: 'INVALID_RECORD' });
    try {
      await ref.update({ ['receipts/' + uid]: state });
      return state;
    } catch (error) {
      lastError = error;
      if (!String(error.code).toLowerCase().includes('permission')) throw error;
      // A concurrent receipt can arrive after the failed acknowledgement.
      await new Promise(resolve => setTimeout(resolve, 25));
    }
  }
  throw lastError;
}

function newLikeIntent(state, liked) {
  if (state.revision === Number.MAX_SAFE_INTEGER) throw Object.assign(new Error('Like revision exhausted'), { code: 'INVALID_RECORD' });
  return { actionId: counterActionId(), revision: state.revision + 1, liked, previousLiked: state.liked };
}

async function saveLikeIntent(database, uid, id, intent) {
  const ref = database.ref('likes/' + id);
  const actionPath = 'actions/' + uid + '/' + intent.actionId;
  const proof = { revision: intent.revision, liked: intent.liked };
  const changes = {
    count: firebase.database.ServerValue.increment(Number(intent.liked) - Number(intent.previousLiked)),
    ['receipts/' + uid]: { ...proof, actionId: intent.actionId },
    [actionPath]: proof
  };
  if (intent.liked !== intent.previousLiked) {
    changes['users/' + uid] = intent.liked
      ? { liked: true, timestamp: firebase.database.ServerValue.TIMESTAMP } : null;
  }
  try {
    await ref.update(changes);
  } catch (error) {
    // Only an existing, immutable proof can acknowledge this no-op. A missing
    // proof cannot be created without its atomic state/count transition.
    try {
      await ref.update({ [actionPath]: proof });
    } catch (_) {
      const state = await confirmedLikeState(database, uid, id);
      if (state.revision !== intent.revision - 1) return { state, superseded: true };
      throw error;
    }
  }
  return { state: await confirmedLikeState(database, uid, id), superseded: false };
}

function initLikeButtons() {
  document.querySelectorAll('.like-button').forEach(button => {
    const id = button.getAttribute('data-id');
    if (!id) return;
    const countSpan = button.parentElement.querySelector('.like-count');
    const recordRef = db.ref('likes/' + id);
    const userLikeRef = recordRef.child('users/' + userId);
    let saving = false;
    let pending = null;
    let desired = null;
    let observedLiked = false;
    let observedCount = 0;
    let countValid = true;
    let readFailed = false;
    const setState = liked => {
      button.classList.toggle('liked', liked);
      button.setAttribute('aria-pressed', String(liked));
      button.title = liked ? 'Remove your like' : 'Like this article';
    };
    const showCount = () => {
      countSpan.textContent = countValid ? observedCount : '—';
      countSpan.setAttribute('aria-label', countValid ? observedCount + ' likes' : 'Like count unavailable');
    };
    recordRef.child('count').on('value', snapshot => {
      observedCount = snapshot.val() ?? 0;
      countValid = Number.isSafeInteger(observedCount) && observedCount >= 0;
      if (!saving) showCount();
      if (!countValid) {
        button.disabled = true;
        feedback(id, 'This article’s like count needs review.');
      }
    }, error => {
      readFailed = true;
      button.disabled = true;
      reportFirebaseError('like-count-read', error);
      feedback(id, 'The like count is currently unavailable.');
    });
    // Listen only to this visitor's private state, never the parent user map.
    recordRef.child('receipts/' + userId).on('value', () => {}, error => {
      readFailed = true;
      button.disabled = true;
      reportFirebaseError('own-like-receipt-read', error);
      feedback(id, 'Likes are currently unavailable.');
    });
    userLikeRef.on('value', snapshot => {
      observedLiked = snapshot.exists();
      if (saving) return;
      setState(observedLiked);
      button.disabled = readFailed || !countValid;
      button.setAttribute('aria-busy', 'false');
    }, error => {
      readFailed = true;
      button.disabled = true;
      reportFirebaseError('own-like-read', error);
      feedback(id, 'Your like state is currently unavailable.');
    });
    button.addEventListener('click', async () => {
      if (button.disabled || saving) return;
      const restoreFocus = document.activeElement === button;
      if (desired === null) desired = button.getAttribute('aria-pressed') !== 'true';
      saving = true;
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      feedback(id, 'Saving your like…');
      try {
        if (!pending) pending = newLikeIntent(await confirmedLikeState(db, userId, id), desired);
        const result = await saveLikeIntent(db, userId, id, pending);
        setState(result.state.liked);
        feedback(id, result.superseded || result.state.liked !== desired
          ? 'Your like changed in another tab. The current state is shown.'
          : desired ? 'Liked.' : 'Like removed.');
        pending = null;
        desired = null;
      } catch (error) {
        reportFirebaseError('like-update', error);
        feedback(id, !countValid || (observedCount === 0 && observedLiked && desired === false)
          ? 'This article’s like count needs review. Your like was not changed.'
          : 'Could not confirm the like update. Retry to finish the same action.');
      } finally {
        saving = false;
        showCount();
        setState(observedLiked);
        button.disabled = readFailed || !countValid;
        button.setAttribute('aria-busy', 'false');
        if (restoreFocus && !button.disabled
            && (document.activeElement === document.body || document.activeElement === document.documentElement)) {
          button.focus({ preventScroll: true });
        }
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

async function saveShareAction(database, uid, id, actionId) {
  const ref = database.ref('shares/' + id);
  const actionPath = 'actions/' + uid + '/' + actionId;
  try {
    await ref.update({
      ['users/' + uid + '/shared']: true,
      ['users/' + uid + '/timestamp']: firebase.database.ServerValue.TIMESTAMP,
      ['receipts/' + uid]: { actionId },
      [actionPath]: true,
      count: firebase.database.ServerValue.increment(1)
    });
  } catch (error) {
    try { await ref.update({ [actionPath]: true }); }
    catch (_) { throw error; }
  }
}

async function logShareToFirebase(id) {
  if (!userId || !db) return;
  try {
    // One immutable receipt per completed share. Distinct repeat shares still
    // count; resending an uncertain action never allocates a new receipt.
    await saveShareAction(db, userId, id, counterActionId());
  } catch (error) {
    reportFirebaseError('share-count-update', error);
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
