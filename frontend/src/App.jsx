import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import SignIn from './auth';
import Data from './data';
import Protect from './protect';

function App() {

  const [userEmail, setEmail] = useState('');

  useEffect(() => {
    const savedEmail = localStorage.getItem('email');
    if (savedEmail) {
      setEmail(savedEmail);
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('email');
    setEmail('');
  };

  return (
    <Router>
      <div className="bg-dark text-light min-vh-100">
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
          <div className="container">
            <Link className="navbar-brand d-flex align-items-center" to="/">
              <img
                src="/darkocsslogo.svg"
                alt="OCSS Logo"
                width="240"
                height="240"
                className="me-2"
              />
            </Link>
            <button
              className="navbar-toggler"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#navbarSupportedContent"
              aria-controls="navbarSupportedContent"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarSupportedContent">
              <ul className="navbar-nav ms-auto mb-2 mb-lg-0">
                {/* Welcome email text */}
                <div className="text-light py-2" style={{ position: 'absolute', top: 70, right: 0, width: '100%' }}>
                  <div className="container text-end">
                    {userEmail && <h4 className="mb-0" style={{ fontSize: '1.25rem' }}>Welcome, {userEmail}!</h4>}
                  </div>
                </div>
                <li className="nav-item">
                  <Link className="nav-link" to="/">
                    <i className="fas fa-home me-1"></i>
                    Home
                  </Link>
                </li>
                {/* Navigation to data route */}
                {userEmail && (
                  <li className="nav-item">
                    <Link className="nav-link" to="/data">
                      <i className="fas fa-chart-line me-1"></i>
                      Data
                    </Link>
                  </li>
                )}
                <li className="nav-item">
                  {/* Need an about page developed */}
                  <Link className="nav-link" to="/about">
                    <i className="fas fa-info-circle me-1"></i>
                    About
                  </Link>
                </li>
                {/* FireBase SignIn */}
                <li className="nav-item">
                  <Link className="nav-link d-flex align-items-center" to="/">
                    <i className="fas fa-user me-1"></i>
                    {!userEmail ? (
                      <SignIn setEmail={setEmail} />
                    ) : (
                      <button className="nav-link btn btn-link text-grey p-0" onClick={logout}>Logout</button>
                    )}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </nav>
        <div className="container mt-5">
          {/* Centered Heading */}
          <Routes>
            <Route path="/" element={
              <div>
                <div className="text-center">
                  <h1>Welcome to OCSS</h1>
                </div>
                {/* Left-aligned description text */}
                <div className="mt-4">
                  <p>
                    There exists no comprehensive solution to appraise the sentiment of online social media platforms. This is a pressing issue, as the use of these platforms is ubiquitous, especially for members of marginalized communities. Despite endless hours spent using these platforms by everyday users, research of the messages’ contents is not immediately apparent, straightforward, or accessible. Research into the opinions and experiences shared within these communities can offer altruistic opportunities, especially the dissemination of medical outcomes and their success rates.
                  </p>
                  <p>
                    To enable this accessibility, as a juncture of computer science and social science, this website is built with React and Flask to bridge the gap between otherwise unwieldy magnitudes of text data and straightforward sentiment analysis. This project intends to help social scientists analyze these social platforms. The website will likely go on to contain more advanced features within its lifetime, including measuring linguistic trends and interactions between groups on the Internet.
                  </p>
                </div>
              </div>
            } />

            {/* Data Page Route Protected */}
            <Route
              path="/data" element={
                <Protect userEmail={userEmail}>
                  <Data />
                </Protect>} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}
    
export default App;
