(() => {
  const form = document.querySelector('#verification-form');
  if (!form) return;
  const video = document.querySelector('#verification-camera');
  const canvas = document.querySelector('#verification-canvas');
  const field = document.querySelector('#verification-face-data');
  const start = document.querySelector('#verification-start');
  const capture = document.querySelector('#verification-capture');
  const status = document.querySelector('#verification-camera-status');
  let stream = null;
  start.addEventListener('click', async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      status.textContent = 'Camera access is unavailable. Use HTTPS and a supported browser.';
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'user'}, audio: false});
      video.srcObject = stream;
      await video.play();
      capture.disabled = false;
      status.textContent = 'Camera ready. Position one consenting candidate in the frame.';
    } catch (error) {
      status.textContent = error.name === 'NotAllowedError' ? 'Camera permission was denied. Allow camera access and try again.' : 'Could not start the camera. Check that it is connected and not in use by another app.';
    }
  });
  capture.addEventListener('click', () => {
    if (!video.videoWidth || !video.videoHeight) {
      status.textContent = 'Wait until the camera preview is ready, then capture again.';
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    field.value = canvas.toDataURL('image/jpeg', 0.82);
    status.textContent = 'Capture ready. The image will be processed for this verification request.';
  });
  form.addEventListener('submit', event => {
    if (!field.value) {
      event.preventDefault();
      status.textContent = 'Capture a face image before submitting the verification.';
    }
  });
  window.addEventListener('pagehide', () => stream?.getTracks().forEach(track => track.stop()));
})();