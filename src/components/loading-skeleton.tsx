import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function LoadingSkeleton() {
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-1/3" />
            <Skeleton className="h-8 w-1/4 rounded-full" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-6 w-1/4" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      </CardContent>
       <CardFooter className="bg-muted/50 p-4 rounded-b-lg">
         <div className="flex items-start gap-2 w-full">
            <Skeleton className="h-4 w-4 mt-0.5 rounded-full" />
            <div className="space-y-2 w-full">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-1/2" />
            </div>
         </div>
      </CardFooter>
    </Card>
  );
}
