import { Scale } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useI18n } from "@/lib/i18n-context";

const WEIGHTS: { key: string; weight: number }[] = [
  { key: "scoring.w.stage", weight: 20 },
  { key: "scoring.w.value", weight: 20 },
  { key: "scoring.w.fit", weight: 20 },
  { key: "scoring.w.timing", weight: 20 },
  { key: "scoring.w.product", weight: 10 },
  { key: "scoring.w.rep", weight: 10 },
];

export function ScoringLogic({
  open,
  onOpenChange,
  referenceDate,
  globalWinRate,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  referenceDate?: string;
  globalWinRate?: number;
}) {
  const { t } = useI18n();
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto bg-card sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Scale className="h-5 w-5 text-gold" /> {t("scoring.title")}
          </SheetTitle>
          <SheetDescription>{t("scoring.description")}</SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          <section>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {t("scoring.formula.heading")}
            </h4>
            <p className="rounded-md border border-border bg-secondary/40 p-3 text-sm leading-relaxed text-foreground">
              {t("scoring.formula.text")}
            </p>
          </section>

          <section>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {t("scoring.weights.heading")}
            </h4>
            <div className="space-y-2.5">
              {WEIGHTS.map((w) => (
                <div key={w.key} className="rounded-md border border-border bg-secondary/30 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-foreground">{t(w.key)}</span>
                    <span className="tabular rounded bg-gold/15 px-1.5 py-0.5 text-xs font-bold text-gold">
                      {w.weight}%
                    </span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    {t(`${w.key}.desc`)}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {t("scoring.note.heading")}
            </h4>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {["scoring.note.1", "scoring.note.2", "scoring.note.3", "scoring.note.4"].map((k) => (
                <li key={k} className="flex gap-2">
                  <span className="text-gold">·</span>
                  {t(k)}
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {t("scoring.bands.heading")}
            </h4>
            <ul className="space-y-1 text-sm">
              <li className="flex justify-between">
                <span className="text-gold">{t("scoring.bands.high")}</span>
                <span className="text-muted-foreground">{t("scoring.bands.high.note")}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-success">{t("scoring.bands.priority")}</span>
                <span className="text-muted-foreground">{t("scoring.bands.priority.note")}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-warning">{t("scoring.bands.watch")}</span>
                <span className="text-muted-foreground">{t("scoring.bands.watch.note")}</span>
              </li>
              <li className="flex justify-between">
                <span className="text-muted-foreground">{t("scoring.bands.low")}</span>
                <span className="text-muted-foreground">{t("scoring.bands.low.note")}</span>
              </li>
            </ul>
          </section>

          <section>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {t("scoring.explain.heading")}
            </h4>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {[
                "scoring.explain.1",
                "scoring.explain.2",
                "scoring.explain.3",
                "scoring.explain.4",
              ].map((k) => (
                <li key={k} className="flex gap-2">
                  <span className="text-gold">·</span>
                  {t(k)}
                </li>
              ))}
            </ul>
          </section>

          {referenceDate && (
            <p className="text-xs text-muted-foreground">
              {t("scoring.reference", {
                date: referenceDate,
                rate: Math.round((globalWinRate ?? 0) * 100),
              })}
            </p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
