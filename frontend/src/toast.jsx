import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function handleNotify() {
    toast("Topic Clustering Complete!");

    if (Notification.permission === "granted") {
        new Notification("Topic Clustering Complete!", {
            icon: "../public/ocsslogo.svg",
        });
    } else if (Notification.permission !== "denied") {
        Notification.requestPermission().then((permission) => {
            if (permission === "granted") {
                new Notification("Topic Clustering Complete!", {
                    icon: "../public/ocsslogo.svg",
                });
            }
        });
    }
}

export default handleNotify;