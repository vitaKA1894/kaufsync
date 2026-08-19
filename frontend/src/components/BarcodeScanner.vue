<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { scanImageData } from '@undecaf/zbar-wasm';

const emit = defineEmits(['close', 'scan']);

const videoRef = ref(null);
const canvasRef = ref(null);
const scannerActive = ref(true);
let stream = null;
let animationFrameId = null;
let lastScanTime = 0;
let lastCode = null;

// Throttling configuration
const SCAN_INTERVAL_MS = 150;
const DEBOUNCE_MS = 600;
const DEDUPLICATION_MS = 2000;


let lastPollTime = 0;

// Internal state for debouncing
let potentialCode = null;
let potentialCodeFirstSeen = 0;


const startCamera = async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });
        if (videoRef.value) {
            videoRef.value.srcObject = stream;
            // Need to wait until video is playing to start scanning
            videoRef.value.onloadedmetadata = () => {
                videoRef.value.play();
                startScanning();
            };
        }
    } catch (err) {
        console.error("Fehler beim Kamerazugriff:", err);
        // Fallback or error handling can be done here
    }
};

const stopCamera = () => {
    scannerActive.value = false;
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (videoRef.value) {
        videoRef.value.srcObject = null;
    }
};

const closeScanner = () => {
    stopCamera();
    emit('close');
};

const processScannedCode = (code) => {
    const now = Date.now();

    // Deduplication logic (prevent identical scans right after another)
    if (code === lastCode && (now - lastScanTime) < DEDUPLICATION_MS) {
        return;
    }

    // Entprellung (Debouncing) - Verifying code
    if (code !== potentialCode) {
        potentialCode = code;
        potentialCodeFirstSeen = now;
        return;
    }

    if ((now - potentialCodeFirstSeen) >= DEBOUNCE_MS) {
        // Code successfully verified
        lastCode = code;
        lastScanTime = now;
        potentialCode = null; // Reset for next scan

        emit('scan', code);
    }
};

// Dual-Engine approach
const startScanning = () => {
    const video = videoRef.value;
    const canvas = canvasRef.value;
    if (!video || !canvas || !scannerActive.value) return;

    const ctx = canvas.getContext('2d', { willReadFrequently: true });

    let nativeDetector = null;
    if ('BarcodeDetector' in window) {
        try {
            nativeDetector = new window.BarcodeDetector({ formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e'] });
        } catch (e) {
            console.warn("Native BarcodeDetector existiert, aber Formate nicht unterstützt:", e);
        }
    }


    const scanLoop = async (timestamp) => {
        if (!scannerActive.value) return;

        // Throttling to approx 150ms for polling the video stream
        if (timestamp - lastPollTime < SCAN_INTERVAL_MS) {
             animationFrameId = requestAnimationFrame(scanLoop);
             return;
        }
        lastPollTime = timestamp;

        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            let codesFound = 0;
            // Native Engine A
            if (nativeDetector) {
                try {
                    const barcodes = await nativeDetector.detect(video);
                    if (barcodes.length > 0) {
                        codesFound++;
                        processScannedCode(barcodes[0].rawValue);
                        animationFrameId = requestAnimationFrame(scanLoop);
                        return; // Found with native detector, skip fallback
                    }
                } catch (e) {
                    console.error("Native scan error", e);
                }
            }

            // Fallback Engine B (WASM)
            if (codesFound === 0) {
                try {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                    const results = await scanImageData(imageData);
                    if (results && results.length > 0) {
                        const code = typeof results[0].decode === 'function' ? results[0].decode() : results[0].decode; // Get decoded string
                        if (code) {
                            codesFound++;
                            processScannedCode(code);
                        }
                    }
                } catch (e) {
                    console.error("WASM scan error", e);
                }
            }

            // If no codes were found in this frame, reset potentialCode so a brief flash doesn't persist forever
            if (codesFound === 0) {
                potentialCode = null;
                potentialCodeFirstSeen = 0;
            }
        }

        animationFrameId = requestAnimationFrame(scanLoop);
    };

    animationFrameId = requestAnimationFrame(scanLoop);
};

onMounted(() => {
    nextTick(() => {
        startCamera();
    });
});

onBeforeUnmount(() => {
    stopCamera();
});

</script>

<template>
    <div class="scanner-container">
        <!-- Video Stream Layer -->
        <video
            ref="videoRef"
            class="scanner-video"
            autoplay
            playsinline
            muted
        ></video>

        <!-- Hidden Canvas for Image Processing -->
        <canvas ref="canvasRef" style="display: none;"></canvas>

        <!-- UI Overlay Layer -->
        <div class="scanner-overlay">
            <div class="crosshair-container">
                <div class="crosshair-target"></div>
            </div>

            <div class="scanner-header">
                <button class="close-btn ks-icon-btn" @click="closeScanner">
                    <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                </button>
            </div>

            <div class="scanner-footer">
                <p>Scanne den Barcode eines Produkts.</p>
            </div>
        </div>
    </div>
</template>

<style scoped>
.scanner-container {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: #000;
    overflow: hidden;
    border-radius: 20px 20px 0 0;
    display: flex;
    flex-direction: column;
}

.scanner-video {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    z-index: 1;
}

.scanner-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 2;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    pointer-events: none; /* Let clicks pass through except on buttons */
}

.scanner-header {
    display: flex;
    justify-content: flex-end;
    padding: 16px;
    pointer-events: auto; /* Enable clicks on header buttons */
}

.close-btn {
    background: rgba(0, 0, 0, 0.5);
    border-radius: 50%;
    color: white;
}

.close-btn svg { width: 24px; height: 24px; fill: currentColor; }

.crosshair-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}

.crosshair-target {
    width: 250px;
    height: 150px;
    border: 2px solid rgba(255, 255, 255, 0.7);
    border-radius: 12px;
    position: relative;
    box-shadow: 0 0 0 4000px rgba(0, 0, 0, 0.5); /* Semi-transparent background mask */
}

/* Corner markers for the crosshair */
.crosshair-target::before, .crosshair-target::after {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 12px;
}

.scanner-footer {
    padding: 24px;
    text-align: center;
    background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
    color: white;
}

.scanner-footer p {
    margin: 0;
    font-size: 16px;
    font-weight: 500;
}
</style>