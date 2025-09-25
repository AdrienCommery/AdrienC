import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import FinanceCalculator from "./components/FinanceCalculator";
import { Toaster } from "./components/ui/toaster";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<FinanceCalculator />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;