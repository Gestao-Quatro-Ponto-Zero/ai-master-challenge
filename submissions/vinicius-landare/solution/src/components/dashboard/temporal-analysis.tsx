"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import { IconClock, IconCalendar } from "@/components/icons";

interface Props {
  dowData: Record<string, unknown>[];
  hourData: Record<string, unknown>[];
}

const dayLabel: Record<string, string> = {
  Monday: "Seg", Tuesday: "Ter", Wednesday: "Qua",
  Thursday: "Qui", Friday: "Sex", Saturday: "Sáb", Sunday: "Dom",
};

const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export function TemporalAnalysis({ dowData, hourData }: Props) {
  const dowChart = [...dowData]
    .sort((a, b) => dayOrder.indexOf(a.day_of_week as string) - dayOrder.indexOf(b.day_of_week as string))
    .map(d => ({
      day: dayLabel[d.day_of_week as string] || (d.day_of_week as string).substring(0, 3),
      engagement: Number((d.avg_engagement_rate as number).toFixed(4)),
      posts: d.posts as number,
    }));

  const hourChart = hourData.map(d => ({
    hour: `${d.hour}h`,
    engagement: Number((d.avg_engagement_rate as number).toFixed(4)),
    posts: d.posts as number,
  }));

  const bestDay = dowChart.reduce((a, b) => a.engagement > b.engagement ? a : b);
  const bestHour = hourChart.reduce((a, b) => a.engagement > b.engagement ? a : b);

  return (
    <div className="space-y-4">
      {/* Resumo executivo */}
      <div className="bg-gradient-to-r from-[#0F1B2D] to-[#1A2D47] rounded-2xl p-6 text-white">
        <div className="flex items-center gap-2 mb-2">
          <IconClock className="w-5 h-5 text-[#E8734A]" />
          <h3 className="text-base font-semibold">Quando Publicar?</h3>
        </div>
        <p className="text-sm text-white/80 leading-relaxed">
          O melhor dia para publicar é <strong className="text-[#E8734A]">{bestDay.day}</strong> e o melhor horário é <strong className="text-[#E8734A]">{bestHour.hour}</strong>.
          Mas atenção: as diferenças são pequenas. O mais importante é manter <strong className="text-white">consistência</strong> e
          evitar os horários de baixa (15h-16h e 22h-23h).
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Dia da semana */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-1">
              <IconCalendar className="w-4 h-4 text-[#E8734A]" />
              <h3 className="text-base font-semibold text-[#0F1B2D]">Interação por Dia da Semana</h3>
            </div>
            <p className="text-xs text-slate-500 mt-1">Qual dia da semana gera mais interação nas publicações</p>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={dowChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="day" fontSize={11} tick={{ fill: "#64748b" }} />
              <YAxis domain={[19.89, 19.92]} fontSize={10} tick={{ fill: "#64748b" }} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
                formatter={(v: number) => [`${v}%`, "Taxa de Interação"]}
              />
              <Bar dataKey="engagement" fill="#0F1B2D" name="Taxa de Interação" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-3 grid grid-cols-7 gap-1 text-center">
            {dowChart.map((d, i) => (
              <div key={i} className="text-[10px] text-slate-500">
                <div className="font-semibold text-[#0F1B2D]">{d.posts.toLocaleString("pt-BR")}</div>
                posts
              </div>
            ))}
          </div>
        </div>

        {/* Hora do dia */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-1">
              <IconClock className="w-4 h-4 text-[#E8734A]" />
              <h3 className="text-base font-semibold text-[#0F1B2D]">Interação por Hora do Dia</h3>
            </div>
            <p className="text-xs text-slate-500 mt-1">Em quais horários as publicações performam melhor</p>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={hourChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="hour" fontSize={9} tick={{ fill: "#64748b" }} interval={1} />
              <YAxis domain={[19.88, 19.94]} fontSize={10} tick={{ fill: "#64748b" }} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
                formatter={(v: number) => [`${v}%`, "Taxa de Interação"]}
              />
              <Line type="monotone" dataKey="engagement" stroke="#E8734A" strokeWidth={2.5} dot={{ r: 3, fill: "#E8734A" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-3 flex items-center justify-center gap-4 text-[11px] text-slate-500">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-emerald-500 rounded" />
              <span>Picos: 7h, 11h, 18h, 21h</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-red-400 rounded" />
              <span>Evitar: 15h-16h, 22h-23h</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
