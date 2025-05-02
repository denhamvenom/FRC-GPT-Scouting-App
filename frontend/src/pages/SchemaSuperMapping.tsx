// frontend/src/pages/SchemaSuperMapping.tsx

import { useEffect, useState } from "react";

function SchemaSuperMapping() {
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<{ [key: string]: string }>({});
  const [offsets, setOffsets] = useState<{ [key: string]: string[] }>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/schema/super/learn")
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          setHeaders(data.headers);
          setMapping(data.mapping);
          setOffsets(data.offsets);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (header: string, value: string) => {
    setMapping((prev) => ({
      ...prev,
      [header]: value,
    }));
  };

  const handleSave = async () => {
    await fetch("http://localhost:8000/api/schema/super/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mapping: mapping,
        offsets: offsets
      }),
    });
    alert("SuperScouting Schema saved.");
  };

  if (loading) return <div className="text-center p-8">Loading schema...</div>;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">SuperScouting Schema Mapping</h1>
      <table className="w-full table-auto border">
        <thead>
          <tr className="bg-gray-100">
            <th className="border px-4 py-2">Header</th>
            <th className="border px-4 py-2">Mapped Tag</th>
          </tr>
        </thead>
        <tbody>
          {headers.map((header) => (
            <tr key={header}>
              <td className="border px-4 py-2">{header}</td>
              <td className="border px-4 py-2">
                <input
                  className="w-full p-1 border rounded"
                  value={mapping[header] || ""}
                  onChange={(e) => handleChange(header, e.target.value)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button
        onClick={handleSave}
        className="mt-6 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
      >
        Save SuperScouting Schema
      </button>
    </div>
  );
}

export default SchemaSuperMapping;
