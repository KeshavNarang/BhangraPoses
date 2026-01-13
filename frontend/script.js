const video1 = document.getElementById("video1");
const video2 = document.getElementById("video2");
const canvas1 = document.getElementById("canvas1");
const canvas2 = document.getElementById("canvas2");
const fileInput = document.getElementById("userVideoInput");
const uploadBtn = document.getElementById("uploadVideo");

const autoAlignBtn = document.getElementById("autoAlign");
const alignStatus = document.getElementById("alignStatus");
const spinner = alignStatus.querySelector(".spinner");
const check = alignStatus.querySelector(".check");

const referenceSelect = document.getElementById("referenceSelect");

// ---------- Trigger hidden file input ----------
uploadBtn.onclick = () => fileInput.click();

// ---------- Handle video selection ----------
fileInput.onchange = () => {
  if (!fileInput.files.length) return;
  const file = fileInput.files[0];
  video2.src = URL.createObjectURL(file);
  video2.load();
};

// ---------- Reference video selection ----------
function updateReferenceVideo() {
  video1.pause();
  video1.currentTime = 0;
  video1.src = `/references/${referenceSelect.value}`;  // <-- updated path
  video1.load();
}

// Call when dropdown changes
referenceSelect.onchange = updateReferenceVideo;

// Call once on page load
updateReferenceVideo();

// ---------- MediaPipe setup ----------
function resizeCanvasToVideo(video, canvas) {
  if (video.videoWidth === 0 || video.videoHeight === 0) return;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.style.width = video.clientWidth + "px";
  canvas.style.height = video.clientHeight + "px";
}

function setupPose(video, canvas, color) {
  const ctx = canvas.getContext("2d");

  video.onloadedmetadata = () => resizeCanvasToVideo(video, canvas);
  window.addEventListener("resize", () => resizeCanvasToVideo(video, canvas));

  const pose = new Pose({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
  });

  pose.setOptions({
    modelComplexity: 1,
    smoothLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
  });

  pose.onResults((results) => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!results.poseLandmarks) return;

    drawConnectors(ctx, results.poseLandmarks, POSE_CONNECTIONS, { color, lineWidth: 2 });
    drawLandmarks(ctx, results.poseLandmarks, { color: "#FF0066", lineWidth: 1, radius: 2 });
  });

  return {
    video,
    async process() { if (!video.paused && !video.ended) await pose.send({ image: video }); }
  };
}

const p1 = setupPose(video1, canvas1, "#00FFAA");
const p2 = setupPose(video2, canvas2, "#FFD700");

let running = false;
async function renderLoop() {
  if (!running) {
    running = true;
    await p1.process();
    await p2.process();
    running = false;
  }
  requestAnimationFrame(renderLoop);
}

Promise.all([
  new Promise((res) => video1.onloadedmetadata = res),
  new Promise((res) => video2.onloadedmetadata = res)
]).then(() => renderLoop());

// ---------- Play / Pause ----------
document.getElementById("playBoth").onclick = async () => {
  if (video1.paused || video2.paused) {
    video2.currentTime = video1.currentTime;
    await Promise.all([video1.play(), video2.play()]);
  } else {
    video1.pause();
    video2.pause();
  }
};

// ---------- Restart ----------
document.getElementById("restartBoth").onclick = () => {
  video1.pause(); video2.pause();
  video1.currentTime = 0; video2.currentTime = 0;
};

// ---------- Auto-align ----------
autoAlignBtn.onclick = async () => {
  if (!fileInput.files.length) { alert("Please upload a video first!"); return; }

  spinner.classList.remove("hidden");
  check.classList.add("hidden");

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("video", file);
  formData.append("reference", referenceSelect.value);

  try {
    // <-- use relative path for backend
    const response = await fetch("/align", { method: "POST", body: formData });
    if (!response.ok) throw new Error(`Server returned ${response.status}`);

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    video2.src = url;
    video2.load();

    spinner.classList.add("hidden");
    check.classList.remove("hidden");
  } catch (err) {
    console.error(err);
    spinner.classList.add("hidden");
    check.classList.add("hidden");
    alert("❌ Error aligning video. Check backend console.");
  }
};
