'use client';

import { useState, useEffect } from 'react';

interface Poll {
  id: number;
  agency: string;
  date: string;
  results: Record<string, number>;
  sample_size: number;
  method: string | null;
  is_manual_override: boolean;
}

export default function Home() {
  const [polls, setPolls] = useState<Poll[]>([]);
  const [loading, setLoading] = useState(true);
  const [newPoll, setNewPoll] = useState({
    agency: '',
    date: new Date().toISOString().split('T')[0],
    results: '{"party_democratic": 40, "party_republican": 40}',
    sample_size: 1000,
    method: 'CATI',
    is_manual_override: true,
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';

  useEffect(() => {
    fetchPolls();
  }, []);

  const fetchPolls = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/polls`);
      const data = await res.json();
      setPolls(data);
    } catch (err) {
      console.error('Failed to fetch polls:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${apiUrl}/polls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newPoll,
          results: JSON.parse(newPoll.results),
        }),
      });
      if (res.ok) {
        fetchPolls();
        setNewPoll({ ...newPoll, agency: '', results: '{"party_democratic": 40, "party_republican": 40}' });
      }
    } catch (err) {
      alert('Error adding poll. Check JSON format.');
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold text-slate-900">PollAgg B2B Dashboard</h1>
          <p className="text-slate-600">Advanced Statistical Optimizer & Data Management</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Data Entry Section */}
          <section className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-xl font-semibold text-slate-800 mb-6">Manual Poll Entry</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Agency</label>
                  <input
                    type="text"
                    required
                    value={newPoll.agency}
                    onChange={(e) => setNewPoll({ ...newPoll, agency: e.target.value })}
                    className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Date</label>
                  <input
                    type="date"
                    required
                    value={newPoll.date}
                    onChange={(e) => setNewPoll({ ...newPoll, date: e.target.value })}
                    className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Results (JSON)</label>
                  <textarea
                    required
                    rows={3}
                    value={newPoll.results}
                    onChange={(e) => setNewPoll({ ...newPoll, results: e.target.value })}
                    className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border font-mono"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newPoll.is_manual_override}
                    onChange={(e) => setNewPoll({ ...newPoll, is_manual_override: e.target.checked })}
                    className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label className="ml-2 text-sm text-slate-700">Manual Override</label>
                </div>
                <button
                  type="submit"
                  className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors font-medium shadow-md shadow-indigo-200"
                >
                  Add Poll Data
                </button>
              </form>
            </div>
          </section>

          {/* Table Section */}
          <section className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-6 border-b border-slate-200 flex justify-between items-center">
                <h2 className="text-xl font-semibold text-slate-800">Database Records</h2>
                <button 
                  onClick={fetchPolls}
                  className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                >
                  Refresh
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Agency</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Results</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-200">
                    {loading ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-slate-500">Loading data...</td>
                      </tr>
                    ) : polls.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-slate-500">No records found.</td>
                      </tr>
                    ) : (
                      polls.map((poll) => (
                        <tr key={poll.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-900">{poll.agency}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-slate-600">{poll.date}</td>
                          <td className="px-6 py-4 text-slate-600 text-sm font-mono">
                            {JSON.stringify(poll.results)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              poll.is_manual_override ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                            }`}>
                              {poll.is_manual_override ? 'Manual' : 'Auto'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
