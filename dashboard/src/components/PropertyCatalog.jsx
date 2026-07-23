import React, { useState, useEffect } from 'react';
import { Building2, Search, MapPin, DollarSign, Bed, Sparkles, Tag } from 'lucide-react';
import { fetchProperties } from '../api';

export default function PropertyCatalog() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [locationFilter, setLocationFilter] = useState('');
  const [bhkFilter, setBhkFilter] = useState('');
  const [budgetFilter, setBudgetFilter] = useState('');

  const loadProperties = async () => {
    try {
      setLoading(true);
      const data = await fetchProperties({
        location: locationFilter,
        bhk: bhkFilter,
        budget_max: budgetFilter ? parseFloat(budgetFilter) : undefined,
      });
      setProperties(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProperties();
  }, [locationFilter, bhkFilter, budgetFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Property Catalog ({properties.length})</h2>
          <p className="text-sm text-slate-400">
            Real inventory queried live by Riya during qualification calls via the <code className="text-indigo-400 font-mono text-xs">search_properties</code> function.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 glass-panel p-4 rounded-2xl border border-slate-800">
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5">Filter Location</label>
          <div className="relative">
            <MapPin className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              placeholder="e.g. Downtown, Midtown..."
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5">BHK Configuration</label>
          <div className="relative">
            <Bed className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <select
              value={bhkFilter}
              onChange={(e) => setBhkFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">All Configurations</option>
              <option value="1">1 BHK</option>
              <option value="2">2 BHK</option>
              <option value="3">3 BHK</option>
              <option value="4">4 BHK</option>
              <option value="5">5 BHK</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-1.5">Max Budget ($)</label>
          <div className="relative">
            <DollarSign className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="number"
              value={budgetFilter}
              onChange={(e) => setBudgetFilter(e.target.value)}
              placeholder="e.g. 800000"
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Property Cards */}
      {loading ? (
        <div className="text-center py-16 text-slate-400">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p>Loading property catalog...</p>
        </div>
      ) : properties.length === 0 ? (
        <div className="text-center py-16 glass-card rounded-2xl border border-slate-800">
          <Building2 className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-300">No properties matched filters</h3>
          <p className="text-sm text-slate-500 mt-1">Try relaxing your location or budget requirements.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {properties.map((prop) => (
            <div
              key={prop.id}
              className="glass-card rounded-2xl p-5 border border-slate-800/80 hover:border-indigo-500/40 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 text-xs font-semibold">
                    {prop.bhk_config}
                  </span>
                  <span className="font-bold text-lg text-emerald-400">
                    ${prop.price.toLocaleString()}
                  </span>
                </div>

                <h3 className="font-bold text-base text-white group-hover:text-indigo-200 transition-colors mt-1">
                  {prop.title}
                </h3>

                <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-1 mb-3">
                  <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{prop.location}</span>
                </div>

                <p className="text-xs text-slate-300 line-clamp-3 mb-4 leading-relaxed">
                  {prop.description}
                </p>
              </div>

              <div>
                <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  <Sparkles className="w-3 h-3 text-amber-400" />
                  <span>Featured Amenities</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(prop.amenities || []).slice(0, 4).map((a, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-slate-400 text-[11px]"
                    >
                      {a}
                    </span>
                  ))}
                  {(prop.amenities || []).length > 4 && (
                    <span className="px-1.5 py-0.5 rounded-md bg-slate-900 text-slate-500 text-[11px]">
                      +{(prop.amenities.length - 4)} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
