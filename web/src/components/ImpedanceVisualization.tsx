import { useRef, useEffect } from "react";
import * as d3 from "d3";

interface ImpedancePoint {
  frequency: number;
  impedance: number;
}

interface Props {
  data: ImpedancePoint[];
  title?: string;
  width?: number;
  height?: number;
  className?: string;
  peaks?: number[];
  targets?: number[];
}

/**
 * Interactive impedance curve visualization using D3.js
 * Shows input impedance vs frequency with peak markers
 */
export default function ImpedanceVisualization({
  data,
  title = "Input Impedance",
  width = 600,
  height = 280,
  className = "",
  peaks = [],
  targets = [],
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  const margin = { top: 30, right: 30, bottom: 45, left: 55 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(data, d => d.frequency) as [number, number])
      .range([0, innerW]);

    const yMax = d3.max(data, d => d.impedance) || 1;
    const yScale = d3.scaleLinear()
      .domain([0, yMax * 1.1])
      .range([innerH, 0]);

    // Grid lines
    g.append("g")
      .attr("class", "grid")
      .selectAll("line")
      .data(yScale.ticks(5))
      .join("line")
      .attr("x1", 0)
      .attr("x2", innerW)
      .attr("y1", d => yScale(d))
      .attr("y2", d => yScale(d))
      .attr("stroke", "#333")
      .attr("stroke-dasharray", "2,3");

    // Impedance curve
    const line = d3.line<ImpedancePoint>()
      .x(d => xScale(d.frequency))
      .y(d => yScale(d.impedance))
      .curve(d3.curveBasis);

    // Gradient fill
    const gradient = svg.append("defs")
      .append("linearGradient")
      .attr("id", "impedance-gradient")
      .attr("x1", "0%").attr("y1", "0%")
      .attr("x2", "0%").attr("y2", "100%");
    gradient.append("stop").attr("offset", "0%").attr("stop-color", "#8b5cf6").attr("stop-opacity", 0.4);
    gradient.append("stop").attr("offset", "100%").attr("stop-color", "#8b5cf6").attr("stop-opacity", 0.02);

    // Area fill
    const area = d3.area<ImpedancePoint>()
      .x(d => xScale(d.frequency))
      .y0(innerH)
      .y1(d => yScale(d.impedance))
      .curve(d3.curveBasis);

    g.append("path")
      .datum(data)
      .attr("fill", "url(#impedance-gradient)")
      .attr("d", area);

    // Line
    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#8b5cf6")
      .attr("stroke-width", 2)
      .attr("d", line);

    // Target frequency markers
    targets.forEach(freq => {
      g.append("line")
        .attr("x1", xScale(freq))
        .attr("x2", xScale(freq))
        .attr("y1", 0)
        .attr("y2", innerH)
        .attr("stroke", "#22c55e")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "4,3")
        .attr("opacity", 0.7);

      g.append("text")
        .attr("x", xScale(freq))
        .attr("y", -8)
        .attr("text-anchor", "middle")
        .attr("fill", "#22c55e")
        .attr("font-size", "9px")
        .text(`${freq.toFixed(0)}Hz`);
    });

    // Peak markers
    peaks.forEach(freq => {
      const nearest = data.reduce((prev, curr) =>
        Math.abs(curr.frequency - freq) < Math.abs(prev.frequency - freq) ? curr : prev
      );
      const cx = xScale(nearest.frequency);
      const cy = yScale(nearest.impedance);

      g.append("circle")
        .attr("cx", cx)
        .attr("cy", cy)
        .attr("r", 5)
        .attr("fill", "#f59e0b")
        .attr("stroke", "#000")
        .attr("stroke-width", 1.5);

      g.append("text")
        .attr("x", cx)
        .attr("y", cy - 12)
        .attr("text-anchor", "middle")
        .attr("fill", "#f59e0b")
        .attr("font-size", "9px")
        .attr("font-weight", "bold")
        .text(`${freq.toFixed(0)}Hz`);
    });

    // Axes
    g.append("g")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(8).tickFormat(d => `${d}`))
      .call(g => g.select(".domain").attr("stroke", "#555"))
      .call(g => g.selectAll(".tick line").attr("stroke", "#555"))
      .call(g => g.selectAll(".tick text").attr("fill", "#999").attr("font-size", "10px"));

    g.append("g")
      .call(d3.axisLeft(yScale).ticks(5).tickFormat(d3.format(".0f")))
      .call(g => g.select(".domain").attr("stroke", "#555"))
      .call(g => g.selectAll(".tick line").attr("stroke", "#555"))
      .call(g => g.selectAll(".tick text").attr("fill", "#999").attr("font-size", "10px"));

    // Axis labels
    g.append("text")
      .attr("x", innerW / 2)
      .attr("y", innerH + 38)
      .attr("text-anchor", "middle")
      .attr("fill", "#777")
      .attr("font-size", "11px")
      .text("Frequency (Hz)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerH / 2)
      .attr("y", -42)
      .attr("text-anchor", "middle")
      .attr("fill", "#777")
      .attr("font-size", "11px")
      .text("|Z| (Pa·s/m³)");

  }, [data, peaks, targets, width, height]);

  if (data.length === 0) {
    return (
      <div className={`bg-neutral-900 rounded-xl border border-neutral-800 flex items-center justify-center ${className}`} style={{ width, height }}>
        <div className="text-center text-neutral-500">
          <div className="text-2xl mb-2">📊</div>
          <div className="text-xs">Run optimization to see impedance curve</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden ${className}`}>
      {title && (
        <div className="px-4 pt-3 pb-1">
          <div className="text-xs font-medium text-neutral-400">{title}</div>
        </div>
      )}
      <svg ref={svgRef} className="w-full" viewBox={`0 0 ${width} ${height}`} />
    </div>
  );
}
