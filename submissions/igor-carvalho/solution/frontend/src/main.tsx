import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { createApi } from './api/createApi';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App api={createApi()} />
  </React.StrictMode>,
);
