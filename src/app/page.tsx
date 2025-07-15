"use client";

import { useState } from "react";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Leaf } from "lucide-react";
import { getRagResponse } from "./actions";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { LoadingSkeleton } from "@/components/loading-skeleton";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useToast } from "@/hooks/use-toast";

const formSchema = z.object({
  foodItems: z.string().min(3, {
    message: "Please enter at least one food item.",
  }),
});
type FormValues = z.infer<typeof formSchema>;

export default function Home() {
  const [answer, setAnswer] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      foodItems: "",
    },
  });

  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    setIsLoading(true);
    setAnswer(null);
    const { answer, error } = await getRagResponse(data.foodItems);
    setIsLoading(false);

    if (error) {
      toast({
        title: "Error",
        description: error,
        variant: "destructive",
      });
    } else if (answer) {
      setAnswer(answer);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <header className="py-4 px-4 sm:px-6 lg:px-8 border-b bg-card">
        <div className="flex items-center gap-3">
          <div className="bg-primary p-2 rounded-lg">
            <Leaf className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold font-headline">FoodSafe AI</h1>
        </div>
      </header>
      <main className="flex-grow flex flex-col items-center p-4 sm:p-6 lg:p-8">
        <section className="w-full max-w-2xl text-center mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl font-headline">
            Check Your Food's Safety
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Enter the food items you've consumed, and our AI will assess the potential carcinogen risk.
          </p>
        </section>

        <section className="w-full max-w-2xl mb-8">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="foodItems"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="sr-only">Prompt</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Ask the AI anything..."
                        className="resize-none bg-card"
                        rows={4}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" disabled={isLoading} className="w-full text-base font-bold py-6">
                {isLoading ? "Thinking..." : "Ask AI"}
              </Button>
            </form>
          </Form>
        </section>

        <section className="w-full max-w-2xl mt-8">
          {isLoading && <LoadingSkeleton />}
          {answer && !isLoading && (
            <div className="p-4 bg-card rounded shadow text-left whitespace-pre-line">
              {answer}
            </div>
          )}
        </section>
      </main>
      <footer className="text-center p-4 text-xs text-muted-foreground bg-card border-t">
        FoodSafe AI &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
