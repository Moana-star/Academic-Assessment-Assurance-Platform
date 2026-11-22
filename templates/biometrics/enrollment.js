(() => {
  const video = document.querySelector('#camera');
  const canvas = document.querySelector('#canvas');
  const field = document.querySelector('#form-face-data');
  const start = document.querySelector('#start-camera');
  const capture = document.querySelector('#capture');
  const status = document.querySelector('#camera-status');
  const form = document.querySelector('#enroll-form');
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
      status.textContent = 'Camera ready. Capture one consenting student only.';
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
    status.textContent = 'Face capture ready. Save enrollment to process the image.';
  });
  form.addEventListener('submit', event => {
    if (!field.value) {
      event.preventDefault();
      status.textContent = 'Capture a face image before saving enrollment.';
    }
  });
  window.addEventListener('pagehide', () => stream?.getTracks().forEach(track => track.stop()));
})();