// frontend/src/components/Navbar.tsx

import { Link, useLocation } from "react-router-dom";

function Navbar() {
  const location = useLocation();
  
  // Helper to determine if a link is active
  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-blue-800 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold">FRC Scouting AI</span>
            </Link>
          </div>
          
          <div className="flex items-center">
            <div className="flex space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Home
              </Link>
              
              <Link
                to="/workflow"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/workflow") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Workflow
              </Link>
              
              <Link
                to="/setup"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/setup") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Setup
              </Link>
              
              <Link
                to="/field-selection"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                 isActive("/field-selection") 
                ? "bg-blue-900 text-white" 
                : "text-gray-200 hover:bg-blue-700"
              }`}
              >
                Field Selection
              </Link>
              
              <Link
                to="/validation"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/validation") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Validation
              </Link>
              
              <Link
                to="/picklist"
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  isActive("/picklist") 
                    ? "bg-blue-900 text-white" 
                    : "text-gray-200 hover:bg-blue-700"
                }`}
              >
                Picklist
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;