import { useId, useState } from 'react';
import type { Overview } from '../../api/types';
import { calendarDate } from '../../lib/format';

export function ActivityChart({ days }: { days: Overview['statistics']['days'] }) {
  const [period, setPeriod] = useState(14);
  const gradient = useId();
  const data = days.slice(-period);
  const max = Math.max(4, ...data.map((day) => day.count));
  const points = data.map((day, index) => [
    45 + (index / (data.length - 1)) * 630,
    180 - (day.count / max) * 135,
  ]);
  const line = points.map(([x, y], index) => `${index ? 'L' : 'M'} ${x} ${y}`).join(' ');
  return (
    <section className="card chart-card">
      <header className="section-heading">
        <div>
          <h2>Ритм команды</h2>
          <p>Созданные задачи · по дням UTC</p>
        </div>
        <div className="segmented" aria-label="Период графика">
          {[7, 14].map((value) => (
            <button
              key={value}
              aria-pressed={period === value}
              className={period === value ? 'selected' : ''}
              onClick={() => setPeriod(value)}
            >
              {value} дней
            </button>
          ))}
        </div>
      </header>
      <div className="chart-total">
        <strong>{data.reduce((total, day) => total + day.count, 0)}</strong>
        <span>новых задач за период</span>
        <span className="chart-legend">
          <i />
          Создано
        </span>
      </div>
      <svg
        className="activity-chart"
        viewBox="0 0 710 225"
        role="img"
        aria-label={`Создание задач за ${period} дней: ${data.map((day) => `${calendarDate(day.date)} — ${day.count}`).join(', ')}`}
      >
        <defs>
          <linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8271f5" stopOpacity=".22" />
            <stop offset="100%" stopColor="#8271f5" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3, 4].map((step) => (
          <g key={step}>
            <line
              x1="45"
              y1={180 - step * 33.75}
              x2="675"
              y2={180 - step * 33.75}
              stroke="#edeef5"
              strokeDasharray="4 5"
            />
            <text x="25" y={184 - step * 33.75} textAnchor="end">
              {Math.round((max * step) / 4)}
            </text>
          </g>
        ))}
        <path d={`${line} L 675 180 L 45 180 Z`} fill={`url(#${gradient})`} />
        <path d={line} fill="none" stroke="#8271f5" strokeWidth="3" strokeLinejoin="round" />
        {points.map(([x, y], index) => (
          <g key={data[index].date}>
            <circle cx={x} cy={y} r="4" fill="#8271f5" stroke="white" strokeWidth="2">
              <title>
                {calendarDate(data[index].date)}: {data[index].count}
              </title>
            </circle>
            {index % (period === 14 ? 2 : 1) === 0 && (
              <text x={x} y="212" textAnchor="middle">
                {calendarDate(data[index].date)}
              </text>
            )}
          </g>
        ))}
      </svg>
    </section>
  );
}
