import React from "react";

interface PicklistMessageBannersProps {
  error: string | null;
  successMessage: string | null;
}

export const PicklistMessageBanners: React.FC<PicklistMessageBannersProps> = ({
  error,
  successMessage,
}) => {
  return (
    <>
      {error && (
        <div className="p-3 mb-4 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-3 mb-4 bg-green-100 text-green-700 rounded">
          {successMessage}
        </div>
      )}
    </>
  );
};