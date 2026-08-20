import re

with open('frontend/src/components/BarcodeScanner.vue', 'r') as f:
    content = f.read()

# Fix the duplicate requestAnimationFrame lines at the end of scanLoop
fixed = content.replace("""        animationFrameId = requestAnimationFrame(scanLoop);
    };
animationFrameId = requestAnimationFrame(scanLoop);
    };

    animationFrameId = requestAnimationFrame(scanLoop);
};""", """        animationFrameId = requestAnimationFrame(scanLoop);
    };

    animationFrameId = requestAnimationFrame(scanLoop);
};""")

with open('frontend/src/components/BarcodeScanner.vue', 'w') as f:
    f.write(fixed)
