import React, { useState, useEffect } from 'react';
import SignIn from './auth';

function App() {

  const [userEmail, setUserEmail] = useState('');

  useEffect(() => {
    const savedEmail = localStorage.getItem('email');
    if (savedEmail) {
      setUserEmail(savedEmail);
    }
  }, []);

  const logout = () => {
    localStorage.removeItem('email');
    setUserEmail('');
  };

  return (
    <div className="bg-dark text-light min-vh-100">
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
        <div className="container">
          <a className="navbar-brand d-flex align-items-center" href="#">
            <img
              src="/darkocsslogo.svg"
              alt="OCSS Logo"
              width="240"
              height="240"
              className="me-2"
            />
          </a>
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
              <li className="nav-item">
                <a className="nav-link" href="#">
                  <i className="fas fa-home me-1"></i>
                  Home
                </a>
              </li>
              <li className="nav-item">
                <a className="nav-link" href="#">
                  <i className="fas fa-info-circle me-1"></i>
                  About
                </a>
              </li>
              {/* FireBase SignIn */}
              <li className="nav-item">
                <a className="nav-link d-flex align-items-center" href="#">
                  <i className="fas fa-user me-1"></i>
                  {!userEmail ? (
                    <SignIn setUserEmail={setUserEmail} />  
                    ) : (
                    <button className="nav-link btn btn-link text-grey p-0" onClick={logout}>Logout</button>
                  )}                
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      <div className="container mt-5">
        {/* Centered Heading */}
        
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

        {/* Temp Welcome, should route to logged in */}
        <div className="text-center">
          {userEmail && <h2>Welcome, {userEmail}!</h2>}
        </div>

      </div>
    </div>

  );
}

export default App;
