import React, { useState, useEffect } from 'react';
import { Building2, Search, MapPin, DollarSign, Bed, Sparkles } from 'lucide-react';
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-2xl font-extrabold text-[#191512] tracking-tight">Verified Property Catalog ({properties.length})</h2>
          <p className="text-xs text-[#6b635b] mt-0.5">
            Real inventory queried live by Riya during qualification calls via the <code className="text-[#b83226] bg-[#feece8] px-1.5 py-0.5 rounded font-mono text-[11px]">search_properties</code> function.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-[#ffffff] p-4 rounded-2xl border border-[#ede5da] shadow-sm">
        <div>
          <label className="block text-xs font-bold text-[#44403c] mb-1.5">Filter by Location</label>
          <div className="relative">
            <MapPin className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#a8a29e]" />
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              placeholder="e.g. Downtown, Midtown..."
              className="w-full pl-9 pr-3 py-2 bg-[#fbf8f3] border border-[#ede5da] rounded-xl text-xs text-[#191512] placeholder-[#a8a29e] focus:outline-none focus:border-[#d94336]"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#44403c] mb-1.5">BHK Configuration</label>
          <div className="relative">
            <Bed className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#a8a29e]" />
            <select
              value={bhkFilter}
              onChange={(e) => setBhkFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-[#fbf8f3] border border-[#ede5da] rounded-xl text-xs font-semibold text-[#191512] focus:outline-none focus:border-[#d94336]"
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
          <label className="block text-xs font-bold text-[#44403c] mb-1.5">Max Budget ($)</label>
          <div className="relative">
            <DollarSign className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#a8a29e]" />
            <input
              type="number"
              value={budgetFilter}
              onChange={(e) => setBudgetFilter(e.target.value)}
              placeholder="e.g. 800000"
              className="w-full pl-9 pr-3 py-2 bg-[#fbf8f3] border border-[#ede5da] rounded-xl text-xs text-[#191512] placeholder-[#a8a29e] focus:outline-none focus:border-[#d94336]"
            />
          </div>
        </div>
      </div>

      {/* Property Cards */}
      {loading ? (
        <div className="text-center py-20 text-[#6b635b]">
          <div className="w-8 h-8 border-2 border-[#d94336] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm font-medium">Loading property listings...</p>
        </div>
      ) : properties.length === 0 ? (
        <div className="text-center py-16 masal-card p-8 border border-[#ede5da]">
          <Building2 className="w-12 h-12 text-[#a8a29e] mx-auto mb-3" />
          <h3 className="text-base font-bold text-[#191512]">No properties found</h3>
          <p className="text-xs text-[#6b635b] mt-1">Try widening your price range or location filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {properties.map((prop) => (
            <div
              key={prop.id}
              className="masal-card p-6 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#f4ede4] text-[#191512] border border-[#e8dfd2] text-xs font-bold">
                    {prop.bhk_config}
                  </span>
                  <span className="font-extrabold text-lg text-[#191512]">
                    ${prop.price.toLocaleString()}
                  </span>
                </div>

                <h3 className="font-extrabold text-base text-[#191512] group-hover:text-[#d94336] transition-colors mt-1">
                  {prop.title}
                </h3>

                <div className="flex items-center gap-1.5 text-xs text-[#78716c] mt-1 mb-3 font-medium">
                  <MapPin className="w-3.5 h-3.5 text-[#d94336]" />
                  <span>{prop.location}</span>
                </div>

                <p className="text-xs text-[#57534e] line-clamp-3 mb-4 leading-relaxed">
                  {prop.description}
                </p>
              </div>

              <div>
                <div className="flex items-center gap-1 text-[11px] font-bold text-[#78716c] uppercase tracking-wider mb-2">
                  <Sparkles className="w-3 h-3 text-[#d97706]" />
                  <span>Key Amenities</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(prop.amenities || []).slice(0, 4).map((a, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-[#fbf8f3] border border-[#ede5da] text-[#57534e] text-[11px] font-medium"
                    >
                      {a}
                    </span>
                  ))}
                  {(prop.amenities || []).length > 4 && (
                    <span className="px-1.5 py-0.5 rounded-md bg-[#f4ede4] text-[#78716c] text-[11px] font-medium">
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
