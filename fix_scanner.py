import re

with open('frontend/src/components/BarcodeScanner.vue', 'r') as f:
    content = f.read()

# Fix 1: Throttle logic
# We need to maintain a separate timestamp for the last polling attempt, rather than using lastScanTime which is only for successful scans.

throttle_fix = """
let lastPollTime = 0;

// Internal state for debouncing
let potentialCode = null;
let potentialCodeFirstSeen = 0;
"""
content = content.replace("// Internal state for debouncing\nlet potentialCode = null;\nlet potentialCodeFirstSeen = 0;", throttle_fix)

scan_loop_fix = """
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
                        const code = results[0].decode; // Get decoded string
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
"""

# Replace the old scan loop
content = re.sub(r'const scanLoop = async \(timestamp\) => \{.*?(?=animationFrameId = requestAnimationFrame\(scanLoop\);\n    };)', scan_loop_fix, content, flags=re.DOTALL)

with open('frontend/src/components/BarcodeScanner.vue', 'w') as f:
    f.write(content)
