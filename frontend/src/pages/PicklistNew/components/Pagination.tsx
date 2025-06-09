// frontend/src/pages/PicklistNew/components/Pagination.tsx

import React from "react";
import { PaginationProps } from "../types";

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  teamsPerPage,
  totalTeams,
  onPageChange,
  onTeamsPerPageChange,
}) => {
  const handleTeamsPerPageChange = (newTeamsPerPage: number) => {
    // Calculate the first team currently visible
    const firstTeamOnCurrentPage = (currentPage - 1) * teamsPerPage + 1;
    const newPage = Math.ceil(firstTeamOnCurrentPage / newTeamsPerPage);
    const maxNewPage = Math.ceil(totalTeams / newTeamsPerPage);
    
    // Update teams per page and adjust current page
    onTeamsPerPageChange(newTeamsPerPage);
    onPageChange(Math.max(1, Math.min(newPage, maxNewPage)));
  };

  const renderPageNumbers = () => {
    const pageNumbers = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i);
      }
    } else {
      // Show pages around current page
      let startPage, endPage;
      
      if (currentPage <= 3) {
        startPage = 1;
        endPage = maxVisiblePages;
      } else if (currentPage >= totalPages - 2) {
        startPage = totalPages - maxVisiblePages + 1;
        endPage = totalPages;
      } else {
        startPage = currentPage - 2;
        endPage = currentPage + 2;
      }

      for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(i);
      }
    }

    return pageNumbers.map(pageNum => (
      <button
        key={pageNum}
        onClick={() => onPageChange(pageNum)}
        className={`px-3 py-1 mx-1 rounded ${
          currentPage === pageNum 
            ? "bg-blue-600 text-white" 
            : "text-blue-600 hover:bg-blue-50"
        }`}
      >
        {pageNum}
      </button>
    ));
  };

  return (
    <>
      {/* Top pagination controls */}
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 py-2 border-b border-t">
        <div className="mb-2 sm:mb-0">
          <span className="mr-2">Teams per page:</span>
          <select
            value={teamsPerPage}
            onChange={(e) => handleTeamsPerPageChange(parseInt(e.target.value))}
            className="border rounded p-1"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="15">15</option>
            <option value="25">25</option>
            <option value="50">50</option>
          </select>
        </div>

        <div className="flex items-center">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className={`px-2 py-1 rounded ${
              currentPage === 1 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="First page"
          >
            &laquo;
          </button>
          
          <button
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className={`px-3 py-1 rounded ${
              currentPage === 1 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="Previous page"
          >
            &lsaquo;
          </button>

          <span className="mx-2">
            Page {currentPage} of {totalPages || 1}
          </span>

          <button
            onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage >= totalPages}
            className={`px-3 py-1 rounded ${
              currentPage >= totalPages 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="Next page"
          >
            &rsaquo;
          </button>
          
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage >= totalPages}
            className={`px-2 py-1 rounded ${
              currentPage >= totalPages 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="Last page"
          >
            &raquo;
          </button>
        </div>

        <div className="mt-2 sm:mt-0 text-sm text-gray-500">
          {totalTeams > 0 ? (
            <span>
              Showing{" "}
              {Math.min((currentPage - 1) * teamsPerPage + 1, totalTeams)}
              -{Math.min(currentPage * teamsPerPage, totalTeams)} of{" "}
              {totalTeams} teams
            </span>
          ) : (
            <span>No teams to display</span>
          )}
        </div>
      </div>

      {/* Bottom pagination for convenience with longer lists */}
      {totalPages > 1 && (
        <div className="mt-4 flex justify-center">
          <button
            onClick={() => onPageChange(1)}
            disabled={currentPage === 1}
            className={`px-2 py-1 rounded ${
              currentPage === 1 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="First page"
          >
            &laquo;
          </button>
          
          <button
            onClick={() => onPageChange(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className={`px-3 py-1 rounded ${
              currentPage === 1 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="Previous page"
          >
            &lsaquo;
          </button>

          {renderPageNumbers()}

          <button
            onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage >= totalPages}
            className={`px-3 py-1 rounded ${
              currentPage >= totalPages 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="Next page"
          >
            &rsaquo;
          </button>
          
          <button
            onClick={() => onPageChange(totalPages)}
            disabled={currentPage >= totalPages}
            className={`px-2 py-1 rounded ${
              currentPage >= totalPages 
                ? "text-gray-400" 
                : "text-blue-600 hover:bg-blue-50"
            }`}
            title="Last page"
          >
            &raquo;
          </button>
        </div>
      )}
    </>
  );
};