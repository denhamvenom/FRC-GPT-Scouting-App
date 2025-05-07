// frontend/src/App.tsx (update)

// Update to existing App.tsx file

import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Setup from "./pages/Setup";
import FieldSelection from "./pages/FieldSelection";
import Workflow from "./pages/Workflow";
import Validation from "./pages/Validation";
import PicklistNew from "./pages/PicklistNew"; // New component
import UnifiedDatasetBuilder from "./pages/UnifiedDatasetBuilder"; // New component for dataset building
import Navbar from "./components/Navbar";

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow bg-gray-50">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/setup" element={<Setup />} />
            <Route path="/field-selection" element={<FieldSelection />} />
            <Route path="/workflow" element={<Workflow />} />
            <Route path="/validation" element={<Validation />} />
            <Route path="/picklist" element={<PicklistNew />} />
            <Route path="/build-dataset" element={<UnifiedDatasetBuilder />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;