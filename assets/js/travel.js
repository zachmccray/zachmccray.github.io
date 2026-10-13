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
  
  firebase.initializeApp(firebaseConfig);
  const db = firebase.database();
  let userId = null;
  
  // Sign in anonymously
  firebase.auth().signInAnonymously()
    .then(userCredential => {
      userId = userCredential.user.uid;
      console.log("Signed in anonymously as:", userId);
      initLikeButtons();
      initShareCounts();
    })
    .catch(error => {
      console.error("Firebase Auth failed:", error);
    });
  
  // Handle like button behavior
  function initLikeButtons() {
    document.querySelectorAll(".like-button").forEach(button => {
      const id = button.getAttribute("data-id");
      if (!id) return;
  
      const countSpan = button.parentElement.querySelector(".like-count");
      const userLikeRef = db.ref("likes/" + id + "/users/" + userId);
      const countRef = db.ref("likes/" + id + "/count");
  
      // Real-time like count updates
      countRef.on("value", snapshot => {
        countSpan.textContent = snapshot.val() || 0;
      });
  
      // Set initial state
      userLikeRef.once("value").then(snapshot => {
        if (snapshot.exists()) {
          button.classList.add("liked");
          button.title = "You already liked this";
        } else {
          button.title = "Click to like this";
        }
      });
  
      // Toggle like on click
      button.addEventListener("click", () => {
        userLikeRef.once("value").then(snapshot => {
          if (snapshot.exists()) {
            // UNLIKE
            userLikeRef.remove();
            countRef.transaction(current => Math.max((current || 1) - 1, 0));
            button.classList.remove("liked");
            button.title = "Click to like this";
          } else {
            // LIKE
            userLikeRef.set({
              liked: true,
              timestamp: firebase.database.ServerValue.TIMESTAMP
            });
            countRef.transaction(current => (current || 0) + 1);
            button.classList.add("liked");
            button.title = "You already liked this";
          }
        });
      });
    });
  }
  
  // Share post via Web Share API or clipboard fallback
  function sharePost(url, id = null) {
    const shareData = {
      title: document.title,
      text: "Check out this post!",
      url: url
    };
  
    if (navigator.share) {
      navigator.share(shareData)
        .then(() => {
          console.log("Shared via Web Share API");
          if (id) logShareToFirebase(id);
        })
        .catch(err => console.error("Share failed:", err));
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(url)
        .then(() => {
          alert("Link copied to clipboard!");
          if (id) logShareToFirebase(id);
        })
        .catch(err => console.error("Clipboard copy failed:", err));
    }
  }
  
  // Log share action in Firebase
  function logShareToFirebase(id) {
    if (!userId) {
      console.warn("User not authenticated yet, skipping share log.");
      return;
    }
  
    console.log("Logging share for ID:", id);
    const shareRef = db.ref("shares/" + id + "/users/" + userId);
    const countRef = db.ref("shares/" + id + "/count");
  
    shareRef.set({
      shared: true,
      timestamp: firebase.database.ServerValue.TIMESTAMP
    });
    countRef.transaction(current => (current || 0) + 1);
  }
  
  // Real-time share count updates
  function initShareCounts() {
    document.querySelectorAll(".share-button").forEach(button => {
      const id = button.getAttribute("data-id");
      if (!id) return;
  
      const countSpan = button.parentElement.querySelector(".share-count");
      const countRef = db.ref("shares/" + id + "/count");
  
      countRef.on("value", snapshot => {
        countSpan.textContent = snapshot.val() || 0;
      });
    });
  }  