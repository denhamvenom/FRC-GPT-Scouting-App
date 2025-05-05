// frontend/src/App.tsx (update)

import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Setup from "./pages/Setup";
import FieldSelection from "./pages/FieldSelection";
import Workflow from "./pages/Workflow";
import Validation from "./pages/Validation";
import PicklistNew from "./pages/PicklistNew"; // Import the new picklist
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
            <Route path="/picklist" element={<PicklistNew />} /> {/* Update to use the new component */}
            </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;