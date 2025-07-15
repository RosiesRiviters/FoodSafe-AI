import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldAlert, ShieldCheck, ShieldX, Info } from 'lucide-react';
import type { AssessCarcinogenRiskOutput } from "@/ai/flows/integrate-custom-chatgpt-model";

interface RiskCardProps {
  result: AssessCarcinogenRiskOutput;
}

const RiskDisplay = ({ risk }: { risk: string }) => {
  const normalizedRisk = risk.toLowerCase();

  const baseBadgeClass = "text-base font-bold px-3 py-1";

  if (normalizedRisk.includes("low")) {
    return (
      <Badge variant="default" className={baseBadgeClass}>
        <ShieldCheck className="mr-2 h-5 w-5" />
        Low Risk
      </Badge>
    );
  }
  if (normalizedRisk.includes("medium")) {
    return (
      <Badge variant="secondary" className={baseBadgeClass}>
        <ShieldAlert className="mr-2 h-5 w-5" />
        Medium Risk
      </Badge>
    );
  }
  if (normalizedRisk.includes("high")) {
    return (
      <Badge variant="destructive" className={baseBadgeClass}>
        <ShieldX className="mr-2 h-5 w-5" />
        High Risk
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className={baseBadgeClass}>
      <Info className="mr-2 h-5 w-5" />
      {risk}
    </Badge>
  );
};

export function RiskCard({ result }: RiskCardProps) {
  return (
    <Card className="w-full max-w-2xl animate-in fade-in-50 duration-500">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-4">
            <CardTitle className="font-headline">Risk Assessment</CardTitle>
            <RiskDisplay risk={result.riskAssessment} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <h3 className="font-semibold font-headline">Explanation</h3>
          <p className="text-muted-foreground leading-relaxed">{result.explanation}</p>
        </div>
      </CardContent>
      <CardFooter className="bg-muted/50 p-4 rounded-b-lg">
        <CardDescription className="text-xs flex items-start gap-2">
          <Info className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
          <span>{result.disclaimer}</span>
        </CardDescription>
      </CardFooter>
    </Card>
  );
}
