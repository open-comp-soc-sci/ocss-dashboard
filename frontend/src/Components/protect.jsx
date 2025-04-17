import React from 'react';
import { Navigate } from 'react-router-dom';

const Protect = ({ children, userEmail }) => {
    //update to check against emails in the firebase database, is this necessary?
    if (!userEmail) {
        return <Navigate to="/" />;
    }
    return children;
};

export default Protect;
