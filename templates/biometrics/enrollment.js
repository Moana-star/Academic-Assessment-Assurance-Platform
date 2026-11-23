(() => {
  const video = document.querySelector('#camera');
  const canvas = document.querySelector('#canvas');
  const faceField = document.querySelector('#form-face-data');
  const fingerprintConsent = document.querySelector('#fingerprint-consent');
  const studentConsent = document.querySelector('#student-consent');
  const faceConsent = document.querySelector('#face-consent');
  const fingerprintButton = document.querySelector('#start-fingerprint');
  const fingerprintStatus = document.querySelector('#fingerprint-status');
  const startCamera = document.querySelector('#start-camera');
  const capture = document.querySelector('#capture');
  const cameraStatus = document.querySelector('#camera-status');
  const form = document.querySelector('#enroll-form');
  let stream = null;

  fingerprintButton.addEventListener('click', () => {
    if (!studentConsent.checked) {
      fingerprintStatus.textContent = 'Confirm the student consent checkbox before continuing.';
      studentConsent.focus();
      return;
    }
    fingerprintConsent.value = 'yes';
    fingerprintStatus.textContent = 'Fingerprint step completed in simulation. Select Save enrollment to store the record.';
    fingerprintStatus.classList.add('success');
    fingerprintButton.textContent = 'Fingerprint ready to save';
    fingerprintButton.disabled = true;
  });

  startCamera.addEventListener('click', async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      cameraStatus.textContent = 'Camera access is unavailable. Use HTTPS and a supported browser.';
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: 'user'}, audio: false});
      video.srcObject = stream;
      await video.play();
      capture.disabled = false;
      cameraStatus.textContent = 'Camera ready. Capture one consenting student only.';
    } catch (error) {
      cameraStatus.textContent = error.name === 'NotAllowedError'
        ? 'Camera permission was denied. Allow camera access and try again.'
        : 'Could not start the camera. Check that it is connected and not in use by another app.';
    }
  });

  capture.addEventListener('click', () => {
    if (!faceConsent.checked) {
      cameraStatus.textContent = 'Separate face-processing consent is required before capture.';
      faceConsent.focus();
      return;
    }
    if (!video.videoWidth || !video.videoHeight) {
      cameraStatus.textContent = 'Wait until the camera preview is ready, then capture again.';
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    faceField.value = canvas.toDataURL('image/jpeg', 0.82);
    cameraStatus.textContent = 'Face image processed in memory. Only the encrypted facial template is stored; the original photo is discarded.';
  });

  form.addEventListener('submit', event => {
    if (!studentConsent.checked || fingerprintConsent.value !== 'yes') {
      event.preventDefault();
      fingerprintStatus.textContent = 'Click Enroll fingerprint before saving the enrollment record.';
      fingerprintStatus.classList.add('warning');
      fingerprintButton.focus();
    }
  });

  window.addEventListener('pagehide', () => stream?.getTracks().forEach(track => track.stop()));
})();
