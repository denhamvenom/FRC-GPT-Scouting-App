import React from 'react';

interface ModalHeaderProps {
  onClose: () => void;
}

const ModalHeader: React.FC<ModalHeaderProps> = ({ onClose }) => {
  return (
    <div className="border-b border-gray-200 p-4 flex justify-between items-center">
      <h3 className="text-xl font-semibold">Team Comparison & Re-Ranking</h3>
      <button
        onClick={onClose}
        className="text-gray-400 hover:text-gray-600 text-2xl"
      >
        ×
      </button>
    </div>
  );
};

export default ModalHeader;