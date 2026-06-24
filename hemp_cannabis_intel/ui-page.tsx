"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { FilterPanel } from "./components/FilterPanel";
import { StatsBar } from "./components/StatsBar";
import { Leaf, Building2, FlaskConical, Sprout, Factory, Package, Truck, Store, TestTubes, Microscope, Filter } from "lucide-react";

const DATA_PATH = "/data";

const CATEGORIES = [
  { key: "HEMP", label: "Hemp", icon: Leaf, color: "green", subTypes: [
    { key: "Seeds_and_Genetics", label: "Seeds & Genetics", icon: Sprout },
    { key: "Growers_and_Cultivation", label: "Growers & Cultivation", icon: Sprout },
    { key: "Processors_and_Extraction", label: "Processors & Extraction", icon: Factory },
    { key: "Manufacturers_and_Formulators", label: "Manufacturers", icon: Package },
    { key: "Handlers_and_Distributors", label: "Handlers & Distributors", icon: Truck },
    { key: "Retail_and_Sales", label: "Retail & Sales", icon: Store },
    { key: "RandD", label: "R&D", icon: FlaskConical },
  ]},
  { key: "CANNABIS", label: "Cannabis", icon: Building2, color: "orange", subTypes: [
    { key: "Seeds_and_Genetics", label: "Seeds & Genetics", icon: Sprout },
    { key: "Growers_and_Cultivation", label: "Growers & Cultivation", icon: Sprout },
    { key: "Processors_and_Extraction", label: "Processors & Extraction", icon: Factory },
    { key: "Manufacturers_and_Formulators", label: "Manufacturers", icon: Package },
    { key: "Handlers_and_Distributors", label: "Handlers & Distributors", icon: Truck },
    { key: "Retail_and_Sales", label: "Retail & Sales", icon: Store },
    { key: "RandD", label: "R&D", icon: FlaskConical },
  ]},
  { key: "ANALYTIC_LABS", label: "Analytic Labs & Testing", icon: TestTubes, color: "blue", subTypes: [
    { key: "Analytic_Labs_and_Testing", label: "Analytic Labs & Testing", icon: Microscope },
    { key: "Growers_and_Cultivation", label: "Growers & Cultivation", icon: Sprout },
    { key: "Processors_and_Extraction", label: "Processors & Extraction", icon: Factory },
    { key: "Manufacturers_and_Formulators", label: "Manufacturers", icon: Package },
    { key: "Seeds_and_Genetics", label: "Seeds & Genetics", icon: Sprout },
    { key: "Handlers_and_Distributors", label: "Handlers & Distributors", icon: Truck },
  ]},
];

type Row = Record<string, string>;

export default function HomePage() {
  const [cat, setCat] = useState("CANNABIS");
  const [sub, setSub] = useState<string | null>(null);
  const [data, setData] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetch(DATA_PATH + "/v2_" + cat + ".json")
      .then((r) => r.ok ? r.json() : [])
      .then((d: Row[]) => setData(d))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [cat]);

  const filtered = useMemo(() => {
    let r = data;
    if (sub) r = r.filter((x: Row) => normalizeType(x.sub_type || "") === sub);
    for (const [c, v] of Object.entries(filters)) {
      if (v) r = r.filter((x: Row) => (x[c] || "").toLowerCase().includes(String(v).toLowerCase()));
    }
    if (search) {
      const q = search.toLowerCase();
      r = r.filter((x: Row) => Object.values(x).some((v) => String(v).toLowerCase().includes(q)));
    }
    return r;
  }, [data, sub, filters, search]);

  const stats = useMemo(() => {
    const byState: Record<string, number> = {};
    const bySub: Record<string, number> = {};
    let hp = 0, he = 0;
    for (const r of filtered) {
      const st = r.state || "";
      const s = r.sub_type || "Other";
      byState[st] = (byState[st] || 0) + 1;
      bySub[s] = (bySub[s] || 0) + 1;
      if (r.phone) hp++;
      if (r.email) he++;
    }
    return { total: filtered.length, hasPhone: hp, hasEmail: he, byState, bySub };
  }, [filtered]);

  const activeCat = CATEGORIES.find((c) => c.key === cat);

  return (
    <div className="h-screen flex flex-col bg-zinc-950 text-zinc-100">
      <header className="shrink-0 border-b border-zinc-800 bg-zinc-900 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-orange-600 flex items-center justify-center text-sm font-black">G</div>
            <div>
              <h1 className="text-base font-bold">GREA Cannabis & Hemp Intel</h1>
              <p className="text-[10px] text-zinc-500">37,429+ licensed operators across 44 states</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-zinc-500">{filtered.length.toLocaleString()} records</span>
            <button onClick={() => setShowFilters(!showFilters)} className={"flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium " + (showFilters ? "bg-orange-600 text-white" : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700")}>
              <Filter className="w-3.5 h-3.5" />Filters
            </button>
          </div>
        </div>
      </header>
      {showFilters && <FilterPanel data={data} filters={filters} onFiltersChange={setFilters} search={search} onSearchChange={setSearch} />}
      <div className="shrink-0 border-b border-zinc-800 bg-zinc-950 px-4">
        <div className="flex items-center gap-2 py-2 overflow-x-auto">
          {CATEGORIES.map((c) => {
            const Icon = c.icon;
            const active = cat === c.key;
            const cls = active
              ? c.color === "green" ? "bg-green-600/20 text-green-400 border border-green-600/30"
                : c.color === "orange" ? "bg-orange-600/20 text-orange-400 border border-orange-600/30"
                : "bg-blue-600/20 text-blue-400 border border-blue-600/30"
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 border border-transparent";
            return (
              <button key={c.key} onClick={() => { setCat(c.key); setSub(null); }} className={"flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap border " + cls}>
                <Icon className="w-4 h-4" />{c.label}
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-1 pb-2 overflow-x-auto">
          <button onClick={() => setSub(null)} className={"px-2.5 py-1 rounded text-[11px] font-medium " + (!sub ? "bg-zinc-700 text-zinc-200" : "text-zinc-500")}>All</button>
          {activeCat?.subTypes.map((s) => (
            <button key={s.key} onClick={() => setSub(s.key)} className={"flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium whitespace-nowrap " + (sub === s.key ? "bg-zinc-700 text-zinc-200" : "text-zinc-500")}>
              <s.icon className="w-3 h-3" />{s.label}
            </button>
          ))}
        </div>
      </div>
      <StatsBar stats={stats} />
      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full"><div className="w-5 h-5 border-2 border-zinc-600 border-t-orange-500 rounded-full animate-spin" /></div>
        ) : (
          <VirtualTable data={filtered} />
        )}
      </div>
    </div>
  );
}

function normalizeType(t: string): string {
  if (!t) return "";
  return t.replace(/ /g, "_").replace(/&/g, "and");
}

function VirtualTable({ data }: { data: Row[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const ROW_H = 28;
  const OVERSCAN = 15;
  const totalH = data.length * ROW_H;

  const onScroll = () => {
    if (containerRef.current) setScrollTop(containerRef.current.scrollTop);
  };

  const start = Math.max(0, Math.floor(scrollTop / ROW_H) - OVERSCAN);
  const visibleCount = containerRef.current ? Math.ceil(containerRef.current.clientHeight / ROW_H) : 50;
  const end = Math.min(data.length, start + visibleCount + OVERSCAN * 2);
  const visible = data.slice(start, end);
  const offsetY = start * ROW_H;

  const cols = [
    { key: "name", label: "Business Name", w: 200 },
    { key: "state", label: "ST", w: 40 },
    { key: "sub_type", label: "Sub-Category", w: 160 },
    { key: "phone", label: "Phone", w: 120 },
    { key: "email", label: "Email", w: 160 },
    { key: "website", label: "Website", w: 130 },
    { key: "year", label: "Year", w: 50 },
    { key: "source", label: "Source", w: 80 },
  ];

  return (
    <>
      <div className="shrink-0 bg-zinc-900 border-b border-zinc-800">
        <div className="flex items-center text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
          {cols.map((c) => (
            <div key={c.key} className="px-3 py-2 border-r border-zinc-800 truncate" style={{ width: c.w }}>{c.label}</div>
          ))}
        </div>
      </div>
      <div ref={containerRef} onScroll={onScroll} className="flex-1 overflow-auto" style={{ position: "relative" }}>
        <div style={{ height: totalH, position: "relative" }}>
          <table className="w-full text-xs border-collapse" style={{ position: "absolute", top: offsetY, left: 0, right: 0 }}>
            <tbody>
              {visible.map((r, i) => {
                const idx = start + i;
                return (
                  <tr key={idx} style={{ height: ROW_H }} className={(idx % 2 === 0 ? "bg-zinc-900/20" : "") + " hover:bg-orange-500/5 border-b border-zinc-800/30"}>
                    <td className="px-3 py-1 truncate font-medium text-zinc-200" style={{ maxWidth: 200 }}>{r.name}</td>
                    <td className="px-3 py-1 font-mono text-[10px] text-zinc-400">{r.state}</td>
                    <td className="px-3 py-1 truncate text-zinc-300" style={{ maxWidth: 160 }}>{r.sub_type}</td>
                    <td className="px-3 py-1">{r.phone ? <a href={"tel:" + r.phone} className="text-orange-400 hover:underline font-mono">{r.phone}</a> : null}</td>
                    <td className="px-3 py-1 truncate" style={{ maxWidth: 160 }}>{r.email ? <a href={"mailto:" + r.email} className="text-orange-400 hover:underline">{r.email}</a> : null}</td>
                    <td className="px-3 py-1 truncate text-[10px]" style={{ maxWidth: 130 }}>{r.website ? <a href={r.website.startsWith("http") ? r.website : "https://" + r.website} target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:underline">{r.website.replace(/^https?:\/\//, "")}</a> : null}</td>
                    <td className="px-3 py-1 text-zinc-500 font-mono">{r.year || ""}</td>
                    <td className="px-3 py-1 text-zinc-500">{r.source || ""}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
