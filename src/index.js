import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';
import "prismjs/themes/prism-okaidia.css";

const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);