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

  const scanner = document.querySelector('#fingerprint-scanner');
  const scanLabel = document.querySelector('#fingerprint-scan-label');
  const progressBar = document.querySelector('.fingerprint-progress');
  const progressFill = document.querySelector('#fingerprint-progress-fill');
  const progressText = document.querySelector('#fingerprint-progress-text');
  let scanTimer = null;
  let progressTimer = null;
  let scanStartedAt = 0;
  let scanning = false;

  const setProgress = value => {
    const progress = Math.max(0, Math.min(100, value));
    progressFill.style.width = progress + '%';
    progressText.textContent = Math.round(progress) + '% complete';
    progressBar.setAttribute('aria-valuenow', String(Math.round(progress)));
  };

  const stopScan = () => {
    if (scanTimer) window.clearTimeout(scanTimer);
    if (progressTimer) window.clearInterval(progressTimer);
    scanTimer = null;
    progressTimer = null;
    scanning = false;
  };

  fingerprintButton.addEventListener('click', () => {
    if (scanning) {
      stopScan();
      scanner.classList.remove('is-scanning');
      setProgress(0);
      scanLabel.textContent = 'Scan cancelled';
      fingerprintStatus.textContent = 'Fingerprint scan cancelled. No fingerprint data was collected. Select Start fingerprint scan to retry.';
      fingerprintStatus.classList.add('warning');
      fingerprintButton.textContent = 'Retry fingerprint scan';
      return;
    }

    if (!studentConsent.checked) {
      fingerprintStatus.textContent = 'Confirm the student consent checkbox before continuing.';
      fingerprintStatus.classList.add('warning');
      studentConsent.focus();
      return;
    }

    try {
      stopScan();
      fingerprintConsent.value = '';
      fingerprintStatus.classList.remove('success', 'warning');
      scanner.classList.remove('is-success');
      scanner.classList.add('is-scanning');
      scanLabel.textContent = 'Scanning fingerprint…';
      fingerprintStatus.textContent = 'Simulated scan in progress. No physical scanner or fingerprint image is being used.';
      fingerprintButton.textContent = 'Cancel scan';
      scanning = true;
      scanStartedAt = Date.now();

      progressTimer = window.setInterval(() => {
        const elapsed = Date.now() - scanStartedAt;
        setProgress(Math.min(95, (elapsed / 2200) * 100));
      }, 50);

      scanTimer = window.setTimeout(() => {
        stopScan();
        setProgress(100);
        scanner.classList.remove('is-scanning');
        scanner.classList.add('is-success');
        scanLabel.textContent = '✓ Simulated scan complete';
        fingerprintConsent.value = 'yes';
        fingerprintStatus.textContent = 'Fingerprint step completed in simulation. A placeholder reference can now be saved; no fingerprint was captured or recognized.';
        fingerprintStatus.classList.add('success');
        fingerprintButton.textContent = 'Fingerprint ready to save';
        fingerprintButton.disabled = true;
      }, 2200);
    } catch (error) {
      stopScan();
      scanner.classList.remove('is-scanning');
      setProgress(0);
      scanLabel.textContent = 'Scan failed';
      fingerprintStatus.textContent = 'The simulated scan could not start. Please try again.';
      fingerprintStatus.classList.add('warning');
      fingerprintButton.textContent = 'Retry fingerprint scan';
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

  form.addEventListener('submit', event => {
    if (!studentConsent.checked || fingerprintConsent.value !== 'yes' || !faceConsent.checked || !faceField.value) {
      event.preventDefault();
      fingerprintStatus.textContent = 'Complete fingerprint enrollment, give separate face consent, and capture the face before saving.';
      fingerprintStatus.classList.add('warning');
      if (fingerprintConsent.value !== 'yes') fingerprintButton.focus(); else if (!faceConsent.checked) faceConsent.focus(); else capture.focus();
    }
  });

  window.addEventListener('pagehide', () => stream?.getTracks().forEach(track => track.stop()));
})();
