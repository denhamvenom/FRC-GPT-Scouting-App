import { useState, useEffect } from "react";
import { Team } from "../types";

interface PicklistPaginationState {
  currentPage: number;
  teamsPerPage: number;
  totalPages: number;
  setCurrentPage: (page: number) => void;
  setTeamsPerPage: (count: number) => void;
}

export function usePicklistPagination(
  picklist: Team[]
): PicklistPaginationState {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [teamsPerPage, setTeamsPerPage] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);

  useEffect(() => {
    setTotalPages(Math.ceil(picklist.length / teamsPerPage));
  }, [picklist.length, teamsPerPage]);

  return {
    currentPage,
    teamsPerPage,
    totalPages,
    setCurrentPage,
    setTeamsPerPage,
  };
}