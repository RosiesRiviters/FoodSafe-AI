"use client";

import { useState } from "react";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Leaf, ToggleLeft, ToggleRight } from "lucide-react";
import { postIngredientsForAnalysis, postBatchProductsForAnalysis } from "./actions";
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
  const [ingredientResults, setIngredientResults] = useState<any[] | null>(null);
  const [batchProducts, setBatchProducts] = useState<{ product: string; ingredients: string }[]>([
    { product: "", ingredients: "" }
  ]);
  const [batchResults, setBatchResults] = useState<any | null>(null);
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const [isBatchMode, setIsBatchMode] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      foodItems: "",
    },
  });

  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    setIsLoading(true);
    setAnswer(null);
    setIngredientResults(null);
    
    try {
      console.log("Submitting ingredients:", data.foodItems);
      const result = await postIngredientsForAnalysis(data.foodItems);
      setIsLoading(false);
      
      if (result.error) {
        console.error("Backend error:", result.error);
        toast({
          title: "Error",
          description: `Backend error: ${result.error}`,
          variant: "destructive",
        });
      } else if (result.ingredients) {
        console.log("Success! Got results:", result.ingredients);
        setIngredientResults(result.ingredients);
        if (result.warning) {
          toast({
            title: "Warning",
            description: result.warning,
            variant: "default",
          });
        }
      } else {
        console.error("Unexpected response format:", result);
        toast({
          title: "Error",
          description: "Unexpected response from backend",
          variant: "destructive",
        });
      }
    } catch (e) {
      console.error("Frontend error:", e);
      setIsLoading(false);
      toast({
        title: "Error",
        description: `Frontend error: ${e instanceof Error ? e.message : "Unknown error"}`,
        variant: "destructive",
      });
    }
  };

  const handleBatchChange = (idx: number, field: "product" | "ingredients", value: string) => {
    setBatchProducts(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p));
  };
  const handleAddProduct = () => {
    setBatchProducts(prev => [...prev, { product: "", ingredients: "" }]);
  };
  const handleRemoveProduct = (idx: number) => {
    setBatchProducts(prev => prev.filter((_, i) => i !== idx));
  };
  const handleBatchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsBatchLoading(true);
    setBatchResults(null);
    const validProducts = batchProducts.filter(p => p.product.trim() && p.ingredients.trim());
    if (validProducts.length === 0) {
      toast({ title: "Error", description: "Please enter at least one product with ingredients.", variant: "destructive" });
      setIsBatchLoading(false);
      return;
    }
    const result = await postBatchProductsForAnalysis(validProducts);
    setIsBatchLoading(false);
    if (result.error) {
      toast({ title: "Error", description: result.error, variant: "destructive" });
    } else {
      setBatchResults(result);
    }
  };

  const toggleMode = () => {
    setIsBatchMode(!isBatchMode);
    // Clear results when switching modes
    setIngredientResults(null);
    setBatchResults(null);
    setAnswer(null);
  };

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <header className="py-4 px-4 sm:px-6 lg:px-8 border-b bg-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary p-2 rounded-lg">
              <Leaf className="h-6 w-6 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold font-headline">FoodSafe AI</h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {isBatchMode ? "Batch Analysis" : "Single Analysis"}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleMode}
              className="flex items-center gap-2"
            >
              {isBatchMode ? (
                <>
                  <ToggleRight className="h-4 w-4" />
                  <span className="text-xs">Switch to Single</span>
                </>
              ) : (
                <>
                  <ToggleLeft className="h-4 w-4" />
                  <span className="text-xs">Switch to Batch</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-grow flex flex-col items-center p-4 sm:p-6 lg:p-8">
        <section className="w-full max-w-2xl text-center mb-8">
          <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl font-headline">
            Check Your Food's Safety
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {isBatchMode 
              ? "Enter multiple products with their ingredients for batch analysis."
              : "Enter the food items you've consumed, and our AI will assess the potential carcinogen risk."
            }
          </p>
        </section>

        {!isBatchMode ? (
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
                          placeholder="Enter ingredients, e.g. bacon, lettuce, tomato"
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
                  {isLoading ? "Analyzing..." : "Analyze Ingredients"}
                </Button>
              </form>
            </Form>
          </section>
        ) : (
          <section className="w-full max-w-2xl mb-8">
            <h3 className="text-xl font-bold mb-4 text-center">Batch Product Analysis</h3>
            <form onSubmit={handleBatchSubmit} className="space-y-4">
              {batchProducts.map((p, idx) => (
                <div key={idx} className="flex gap-2 mb-2">
                  <input
                    type="text"
                    placeholder="Product name"
                    className="flex-1 border rounded px-3 py-2 bg-card"
                    value={p.product}
                    onChange={e => handleBatchChange(idx, "product", e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Ingredients (comma separated)"
                    className="flex-[2] border rounded px-3 py-2 bg-card"
                    value={p.ingredients}
                    onChange={e => handleBatchChange(idx, "ingredients", e.target.value)}
                  />
                  <button 
                    type="button" 
                    onClick={() => handleRemoveProduct(idx)} 
                    className="text-red-600 font-bold px-2 hover:bg-red-50 rounded"
                  >
                    ×
                  </button>
                </div>
              ))}
              <button 
                type="button" 
                onClick={handleAddProduct} 
                className="bg-primary text-white rounded px-4 py-2 font-bold hover:bg-primary/90"
              >
                + Add Product
              </button>
              <Button type="submit" disabled={isBatchLoading} className="w-full text-base font-bold py-6">
                {isBatchLoading ? "Analyzing Batch..." : "Analyze Batch"}
              </Button>
            </form>
          </section>
        )}
        <section className="w-full max-w-2xl mt-8">
          {(!isBatchMode && isLoading) && <LoadingSkeleton />}
          {!isBatchMode && ingredientResults && !isLoading && (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-card rounded shadow">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left">Name</th>
                    <th className="px-4 py-2 text-left">Risk Level</th>
                    <th className="px-4 py-2 text-left">Score</th>
                    <th className="px-4 py-2 text-left">NOVA Group</th>
                    <th className="px-4 py-2 text-left">Source</th>
                    <th className="px-4 py-2 text-left">Explanation</th>
                  </tr>
                </thead>
                <tbody>
                  {ingredientResults.map((item, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-4 py-2 font-semibold">{item.name}</td>
                      <td className="px-4 py-2">{item.risk_level}</td>
                      <td className="px-4 py-2">{item.score}</td>
                      <td className="px-4 py-2">
                        {item.nova_group ? (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            item.nova_group === "1" ? "bg-green-100 text-green-800" :
                            item.nova_group === "2" ? "bg-yellow-100 text-yellow-800" :
                            item.nova_group === "3" ? "bg-orange-100 text-orange-800" :
                            item.nova_group === "4" ? "bg-red-100 text-red-800" :
                            "bg-gray-100 text-gray-800"
                          }`}>
                            {item.nova_group === "1" ? "1 - Unprocessed" :
                             item.nova_group === "2" ? "2 - Processed Ingredients" :
                             item.nova_group === "3" ? "3 - Processed Foods" :
                             item.nova_group === "4" ? "4 - Ultra-processed" :
                             `Group ${item.nova_group}`}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-xs">N/A</span>
                        )}
                      </td>
                      <td className="px-4 py-2">
                        {item.source ? (
                          <span className="text-blue-600">{item.source}</span>
                        ) : (
                          ""
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-pre-line">{item.explanation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {isBatchMode && isBatchLoading && <LoadingSkeleton />}
          {isBatchMode && batchResults && !isBatchLoading && (
            <div>
              {Object.entries(batchResults).map(([product, res]: any) => (
                <div key={product} className="mb-8">
                  <h4 className="font-bold text-lg mb-2">{product}</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full bg-card rounded shadow">
                      <thead>
                        <tr>
                          <th className="px-4 py-2 text-left">Name</th>
                          <th className="px-4 py-2 text-left">Risk Level</th>
                          <th className="px-4 py-2 text-left">Score</th>
                          <th className="px-4 py-2 text-left">NOVA Group</th>
                          <th className="px-4 py-2 text-left">Source</th>
                          <th className="px-4 py-2 text-left">Explanation</th>
                        </tr>
                      </thead>
                      <tbody>
                        {res.ingredients && res.ingredients.map((item: any, idx: number) => (
                          <tr key={idx} className="border-t">
                            <td className="px-4 py-2 font-semibold">{item.name}</td>
                            <td className="px-4 py-2">{item.risk_level}</td>
                            <td className="px-4 py-2">{item.score}</td>
                            <td className="px-4 py-2">
                              {item.nova_group ? (
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  item.nova_group === "1" ? "bg-green-100 text-green-800" :
                                  item.nova_group === "2" ? "bg-yellow-100 text-yellow-800" :
                                  item.nova_group === "3" ? "bg-orange-100 text-orange-800" :
                                  item.nova_group === "4" ? "bg-red-100 text-red-800" :
                                  "bg-gray-100 text-gray-800"
                                }`}>
                                  {item.nova_group === "1" ? "1 - Unprocessed" :
                                   item.nova_group === "2" ? "2 - Processed Ingredients" :
                                   item.nova_group === "3" ? "3 - Processed Foods" :
                                   item.nova_group === "4" ? "4 - Ultra-processed" :
                                   `Group ${item.nova_group}`}
                                </span>
                              ) : (
                                <span className="text-gray-400 text-xs">N/A</span>
                              )}
                            </td>
                            <td className="px-4 py-2">
                              {item.source ? (
                                <span className="text-blue-600">{item.source}</span>
                              ) : (
                                ""
                              )}
                            </td>
                            <td className="px-4 py-2 whitespace-pre-line">{item.explanation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
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
