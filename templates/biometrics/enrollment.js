(() => {
  const video = document.querySelector('#camera');
  const canvas = document.querySelector('#canvas');
  const faceField = document.querySelector('#form-face-data');
  const fingerprintConsent = document.querySelector('#fingerprint-consent');
  const studentConsent = document.querySelector('#student-consent');
  const faceConsent = document.querySelector('#face-consent');
  const fingerprintButton = document.querySelector('#start-fingerprint');
  const touchButton = document.querySelector('#fingerprint-touch');
  const fingerprintStatus = document.querySelector('#fingerprint-status');
  const startCamera = document.querySelector('#start-camera');
  const capture = document.querySelector('#capture');
  const cameraStatus = document.querySelector('#camera-status');
  const form = document.querySelector('#enroll-form');
  let stream = null;

  const scanner = document.querySelector('#fingerprint-scanner');
  const ring = document.querySelector('#fingerprint-ring');
  const scanLabel = document.querySelector('#fingerprint-scan-label');
  const touchHint = document.querySelector('#fingerprint-touch-hint');
  const progressFill = document.querySelector('#fingerprint-progress-fill');
  const progressText = document.querySelector('#fingerprint-progress-text');
  const touchCount = document.querySelector('#fingerprint-touch-count');
  const totalTouches = 5;
  let touches = 0;
  let enrollmentStarted = false;

  const setProgress = () => {
    const percent = Math.round((touches / totalTouches) * 100);
    ring.style.setProperty('--fingerprint-progress', percent + '%');
    ring.setAttribute('aria-valuenow', String(percent));
    progressFill.style.width = percent + '%';
    progressText.textContent = percent + '%';
    touchCount.textContent = touches + ' of ' + totalTouches + ' touches';
  };

  const resetFingerprint = (message) => {
    touches = 0;
    enrollmentStarted = false;
    fingerprintConsent.value = '';
    scanner.classList.remove('is-scanning', 'is-success');
    setProgress();
    scanLabel.textContent = 'Ready to enroll';
    touchHint.textContent = message || 'Start enrollment, then place and lift your finger each time the screen prompts you. Repeat until the circle is full.';
    touchButton.disabled = true;
    touchButton.textContent = 'Touch sensor';
    fingerprintButton.disabled = false;
    fingerprintButton.textContent = 'Start fingerprint enrollment';
  };

  fingerprintButton.addEventListener('click', () => {
    if (!studentConsent.checked) {
      fingerprintStatus.textContent = 'Confirm the student consent checkbox before continuing.';
      fingerprintStatus.classList.add('warning');
      studentConsent.focus();
      return;
    }
    resetFingerprint();
    enrollmentStarted = true;
    scanner.classList.add('is-scanning');
    scanLabel.textContent = 'Fingerprint enrollment in progress';
    touchHint.textContent = 'Place your finger on the simulated sensor, then press Touch sensor. Lift your finger before the next prompt.';
    fingerprintStatus.classList.remove('success', 'warning');
    fingerprintStatus.textContent = 'Demo mode: each Touch sensor press represents one successful sensor reading. No real fingerprint is captured.';
    touchButton.disabled = false;
    fingerprintButton.disabled = true;
    touchButton.focus();
  });

  touchButton.addEventListener('click', () => {
    if (!enrollmentStarted || !studentConsent.checked) return;
    touches = Math.min(totalTouches, touches + 1);
    setProgress();

    if (touches < totalTouches) {
      scanLabel.textContent = 'Reading ' + touches + ' of ' + totalTouches;
      touchHint.textContent = 'Good. Lift your finger, reposition it slightly, then place it again and press Touch sensor.';
      touchButton.textContent = 'Lifted · touch again';
      return;
    }

    enrollmentStarted = false;
    scanner.classList.remove('is-scanning');
    scanner.classList.add('is-success');
    scanLabel.textContent = '✓ Fingerprint enrollment complete';
    touchHint.textContent = 'The progress circle is full. In a real scanner, the device would now confirm that enough fingerprint detail was captured.';
    fingerprintConsent.value = 'yes';
    fingerprintStatus.textContent = 'Simulation completed. The app will save only a clearly labelled placeholder reference, not a fingerprint image or real fingerprint template.';
    fingerprintStatus.classList.remove('warning');
    fingerprintStatus.classList.add('success');
    touchButton.disabled = true;
    touchButton.textContent = 'Enrollment complete';
    fingerprintButton.disabled = false;
    fingerprintButton.textContent = 'Restart demo';
  });

  studentConsent.addEventListener('change', () => {
    if (!studentConsent.checked) {
      resetFingerprint('Consent was unchecked. Confirm consent again before starting.');
      fingerprintStatus.textContent = 'Fingerprint enrollment reset because consent was withdrawn.';
      fingerprintStatus.classList.remove('success');
      fingerprintStatus.classList.add('warning');
    }
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

  faceConsent.addEventListener('change', () => {
    if (!faceConsent.checked) {
      faceField.value = '';
      cameraStatus.textContent = 'Face capture cleared because separate face consent was withdrawn.';
    }
  });

  form.addEventListener('submit', event => {
    if (!studentConsent.checked || fingerprintConsent.value !== 'yes' || !faceConsent.checked || !faceField.value) {
      event.preventDefault();
      fingerprintStatus.textContent = 'Complete all five fingerprint touch steps, give separate face consent, and capture the face before saving.';
      fingerprintStatus.classList.add('warning');
      if (!studentConsent.checked) studentConsent.focus();
      else if (fingerprintConsent.value !== 'yes') fingerprintButton.focus();
      else if (!faceConsent.checked) faceConsent.focus();
      else capture.focus();
    }
  });

  window.addEventListener('pagehide', () => stream?.getTracks().forEach(track => track.stop()));
})();
