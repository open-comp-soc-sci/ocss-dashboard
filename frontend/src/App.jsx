import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Protect from './Components/protect';
import SignIn from './Components/auth';
import Data from './data';
import Results from "./results";

function App() {
  const [userEmail, setEmail] = useState('');
  const [visible, setVisible] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);


  // The SVG images you wish to rotate through
  const svgImages = [
    "/whatdopeopletalkabout.svg",
    "/howdopeoplefeel.svg",
    "/whattermsdopeopleuse.svg"
  ];

  // Controls which layer is active (1 or 2). Each layer is a separate div with its own image.
  const [activeLayer, setActiveLayer] = useState(1);
  // Holds the image source for layer 1 and 2
  const [layer1Image, setLayer1Image] = useState(svgImages[0]);
  const [layer2Image, setLayer2Image] = useState("");

  // Retrieve user email from localStorage on mount (if any)
  useEffect(() => {
    const savedEmail = localStorage.getItem('email');
    if (savedEmail) {
      setEmail(savedEmail);
    }
  }, []);

  // Initial fade-in effect for the image container after 1.5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(true);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  // Rotate through images every 8 seconds after the container has become visible.
  useEffect(() => {
    if (!visible) return;
    const interval = setInterval(() => {
      setCurrentImageIndex(prevIndex => (prevIndex + 1) % svgImages.length);
    }, 6000);
    return () => clearInterval(interval);
  }, [visible, svgImages.length]);

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
                {userEmail && (
                  <li className="nav-item">
                    <Link className="nav-link" to="/data">
                      <i className="fas fa-database me-1"></i>
                      Data
                    </Link>
                  </li>
                )}
                {userEmail && (
                  <li className="nav-item">
                    <Link className="nav-link" to="/results">
                      <i className="fas fa-poll me-1"></i>
                      Results
                    </Link>
                  </li>
                )}
                <li className="nav-item">
                  <Link className="nav-link" to="/about">
                    <i className="fas fa-info-circle me-1"></i>
                    About
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link d-flex align-items-center" to="/">
                    <i className="fas fa-user me-1"></i>
                    {!userEmail ? (
                      <SignIn setEmail={setEmail} />
                    ) : (
                      <button className="nav-link btn btn-link text-grey p-0" onClick={logout}>
                        Logout
                      </button>
                    )}
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </nav>

        <div className="container mt-5">
          <Routes>
            <Route
              path="/"
              element={
                <div>
                  <div className="text-center">
                    <h1>Welcome to Open Computational Social Science</h1>
                  </div>
                  <div className="mt-4">
                    <p>
                      There exists no comprehensive solution to appraise the sentiment of online social media platforms.
                      This is a pressing issue, as the use of these platforms is ubiquitous, especially for members of marginalized communities.
                      Despite endless hours spent using these platforms by everyday users, research of the messages’ contents is not immediately apparent, straightforward, or accessible.
                      Research into the opinions and experiences shared within these communities can offer altruistic opportunities,
                      especially the dissemination of medical outcomes and their success rates.
                    </p>
                    <p>
                      To enable this accessibility, as a juncture of computer science and social science,
                      this website is built with React and Flask to bridge the gap between otherwise unwieldy magnitudes of text data and straightforward sentiment analysis.
                      This project intends to help social scientists analyze these social platforms.
                      The website will likely go on to contain more advanced features within its lifetime, including measuring linguistic trends and interactions between groups on the Internet.
                    </p>
                    <div
                      style={{
                        position: 'relative',
                        textAlign: 'center',
                        // marginTop: '20px',
                        height: '500px',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center'
                      }}
                    >
                      {/* Image container with initial fade in */}
                      <img
                        src={svgImages[currentImageIndex]}
                        alt="Data visualization concept"
                        className="img-fluid"
                        style={{
                          maxHeight: '100%',
                          opacity: visible ? 1 : 0,
                          transition: 'opacity 1s ease-in'
                        }}
                      />
                    </div>
                  </div>
                </div>
              }
            />
            <Route
              path="/about"
              element={
                <div>
                  <h1>What do we want on the about page???</h1>
                </div>
              }
            />
            <Route
              path="/data"
              element={
                <Protect userEmail={userEmail}>
                  <Data />
                </Protect>
              }
            />
            <Route
              path="/results"
              element={
                <Protect userEmail={userEmail}>
                  <Results />
                </Protect>
              }
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;