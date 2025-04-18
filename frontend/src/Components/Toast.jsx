import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function handleNotify(message = "Done!") {
  // in‑page toast
  toast(message);

  // desktop notification
  const showDesktop = () => new Notification(message, {
    icon: "../public/ocsslogo.svg",
  });

  if (Notification.permission === "granted") {
    showDesktop();
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission().then((permission) => {
      if (permission === "granted") {
        showDesktop();
      }
    });
  }
}

export default handleNotify;
