export const subscribeToPush = async (token) => {
    if (!('Notification' in window) || !navigator.serviceWorker) {
        return;
    }

    try {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            return;
        }

        const registration = await navigator.serviceWorker.ready;
        const keyResponse = await fetch('/api/push/public-key');
        const keyData = await keyResponse.json();

        if (keyData && keyData.public_key) {
            const padding = '='.repeat((4 - keyData.public_key.length % 4) % 4);
            const base64 = (keyData.public_key + padding).replace(/\-/g, '+').replace(/_/g, '/');
            const rawData = window.atob(base64);
            const outputArray = new Uint8Array(rawData.length);
            for (let i = 0; i < rawData.length; ++i) {
                outputArray[i] = rawData.charCodeAt(i);
            }

            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: outputArray
            });

            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    endpoint: subscription.endpoint,
                    p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh')))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''),
                    auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth')))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
                })
            });
        } else {
            console.warn("VAPID public key is missing from backend, skipping push subscription.");
        }
    } catch (e) {
        console.error('Error during push subscription:', e);
    }
}
