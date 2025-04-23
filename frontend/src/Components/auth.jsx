import React, { useEffect, useState } from 'react';
import { auth, provider } from "./config"
import { signInWithPopup } from "firebase/auth"

function SignIn() {
    const [value, setValue] = useState('')
    const handleClick = () => {
        provider.setCustomParameters({
            prompt: "select_account"
        });

        signInWithPopup(auth, provider)
            .then((data) => {
                const userEmail = data.user.email
                setValue(userEmail)
                localStorage.setItem("email", userEmail)
                //would be better to update the navbar rather than a full page reload
                window.location.reload();
            })
            .catch((error) => {
                console.error('Unfortunately there was an error signing in: ', error.message);
            });
    }

    useEffect(() => {
        const savedEmail = localStorage.getItem('email');
        if (savedEmail) {
            setValue(savedEmail);
        }
    }, []);

    return (
        <div>
            {value ? (
                <div>
                    {/* Route to logged in page */}
                </div>
            ) : (
                <button className="nav-link btn btn-link text-grey p-0" onClick={handleClick}>Sign In</button>
            )}
        </div>
    );
}

export default SignIn;