"use client";

import { useState, useEffect, useRef } from "react";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Leaf, ToggleLeft, ToggleRight, Instagram } from "lucide-react";
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

const flavorTexts = [
  "2% Reduced Fat!",
  "Just One more Fry",
  "Just put the fries in the bag",
  "Carcinogen Scan AI was developed by a highschool student as part of the IB Personal Project",
  "Its raining Taco's!!!",
  "What'd you eat for dinner?",
  "Carcinogen: A substance capable of causing cancer within living tissue.",
  "BOO!",
  "Pineapple Pizza",
  "An apple a day keeps the doctor away.",
  "Keeping Hydrated?",
  "Crunching Numbers",
  "Weighing Watermelons",
  "Catching Carbs",
  "Spinning up artificial brains.",
  "Insta Below!!!",
  "Know it all-gorithm",
  "Sequencing Salsa",
  "Optimizing Oatmeal",
  "Can u smell the butter?",
  "A or B day?",
  "C Lunch sucks!",
  "Salad Bar today.",
  "There was a second page!"
];

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
  const [buttonText, setButtonText] = useState("Analyze Ingredients");
  const [batchButtonText, setBatchButtonText] = useState("Analyze Batch");
  const flavorTextTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [aiInputError, setAiInputError] = useState<string | null>(null);
  
  // History state
  interface HistoryItem {
    id: string;
    timestamp: Date;
    input: string;
    output: any; // Can be ingredientResults or batchResults
    isBatch: boolean;
  }
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      foodItems: "",
    },
  });

  // Handle history item selection
  const handleHistorySelect = (item: HistoryItem) => {
    setSelectedHistoryId(item.id);
    
    // Clear AI input error when selecting history
    setAiInputError(null);
    
    // Set the appropriate mode
    if (item.isBatch) {
      setIsBatchMode(true);
      // Parse the batch input and set batch products
      const products = item.input.split(" | ").map(prod => {
        const [product, ...ingredientParts] = prod.split(": ");
        return {
          product: product || "",
          ingredients: ingredientParts.join(": ") || ""
        };
      });
      setBatchProducts(products.length > 0 ? products : [{ product: "", ingredients: "" }]);
      setBatchResults(item.output);
      setIngredientResults(null);
    } else {
      setIsBatchMode(false);
      // Set the form input value
      form.setValue("foodItems", item.input);
      setIngredientResults(item.output);
      setBatchResults(null);
    }
    
    // Clear any loading states
    setIsLoading(false);
    setIsBatchLoading(false);
    setButtonText("Analyze Ingredients");
    setBatchButtonText("Analyze Batch");
  };

  // Clear timeout on unmount
  useEffect(() => {
    return () => {
      if (flavorTextTimeoutRef.current) {
        clearTimeout(flavorTextTimeoutRef.current);
      }
    };
  }, []);

  // Function to detect if input is vague
  const isVagueInput = (input: string): { isVague: boolean; suggestions: string[] } => {
    const trimmed = input.trim();
    const words = trimmed.split(/\s+/).filter(w => w.length > 0);
    
    // Very short inputs (less than 10 characters) are likely vague
    if (trimmed.length < 10) {
      return {
        isVague: true,
        suggestions: ["brand name", "specific type", "ingredients list"]
      };
    }
    
    // Single word inputs are likely vague (unless they're very long compound words)
    if (words.length === 1 && trimmed.length < 20) {
      return {
        isVague: true,
        suggestions: ["brand name", "specific variety", "ingredients"]
      };
    }
    
    // Check for common vague patterns
    const vaguePatterns = [
      /^(cereal|bread|meat|cheese|fruit|vegetable|snack|drink|beverage)$/i,
      /^(food|item|product|ingredient)$/i
    ];
    
    for (const pattern of vaguePatterns) {
      if (pattern.test(trimmed)) {
        return {
          isVague: true,
          suggestions: ["brand name", "specific type", "ingredients list"]
        };
      }
    }
    
    // Check if it contains specific details (brand names, types, etc.)
    const hasSpecificDetails = 
      /[A-Z][a-z]+'s/.test(trimmed) || // Brand names like "Cap'n"
      words.length >= 3 || // Multiple words suggest specificity
      /\d/.test(trimmed) || // Numbers suggest specificity
      /(organic|natural|whole|reduced|low|high|free|no)/i.test(trimmed); // Descriptive terms
    
    if (!hasSpecificDetails && words.length <= 2) {
      return {
        isVague: true,
        suggestions: ["brand name", "specific variety", "ingredients"]
      };
    }
    
    return { isVague: false, suggestions: [] };
  };

  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    setIsLoading(true);
    setAnswer(null);
    setIngredientResults(null);
    
    // Clear any existing timeout
    if (flavorTextTimeoutRef.current) {
      clearTimeout(flavorTextTimeoutRef.current);
    }
    
    // Check if input is vague (don't clear previous vague warning yet)
    const vagueCheck = isVagueInput(data.foodItems);
    if (vagueCheck.isVague) {
      const suggestion1 = vagueCheck.suggestions[0] || "brand name";
      const suggestion2 = vagueCheck.suggestions[1] || "specific type";
      setAiInputError(`We recommend giving the AI a bit more data, such as ${suggestion1}, or ${suggestion2} to ensure accurate results; but we can roll with this for the time being.`);
    } else {
      // Only clear if the new input is NOT vague
      setAiInputError(null);
    }
    
    // Set initial text
    setButtonText("May take up to 2 minutes");
    
    // After 3-5 seconds, change to random flavor text
    const delay = Math.random() * 2000 + 3000; // 3000-5000ms
    flavorTextTimeoutRef.current = setTimeout(() => {
      const randomFlavor = flavorTexts[Math.floor(Math.random() * flavorTexts.length)];
      setButtonText(randomFlavor);
    }, delay);
    
    try {
      console.log("Submitting ingredients:", data.foodItems);
      const result = await postIngredientsForAnalysis(data.foodItems);
      setIsLoading(false);
      
      // Clear timeout and reset button text
      if (flavorTextTimeoutRef.current) {
        clearTimeout(flavorTextTimeoutRef.current);
      }
      setButtonText("Analyze Ingredients");
      
      if (result.error) {
        console.error("Backend error:", result.error);
        
        // Check if it's a non-food item error
        if (result.error.includes("Non-food items detected") || result.error.toLowerCase().includes("non-food")) {
          setAiInputError("Input food item");
        } else {
          // For other errors, show in toast
          toast({
            title: "Error",
            description: `Backend error: ${result.error}`,
            variant: "destructive",
          });
        }
      } else if (result.ingredients) {
        // Don't clear vague input warning on success - let it persist
        // Only clear if it was a different type of error
        console.log("Success! Got results:", result.ingredients);
        setIngredientResults(result.ingredients);
        
        // Save to history
        const historyItem: HistoryItem = {
          id: `history-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          input: data.foodItems,
          output: result.ingredients,
          isBatch: false,
        };
        setHistory(prev => [historyItem, ...prev]);
        setSelectedHistoryId(historyItem.id);
        
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
      
      // Clear timeout and reset button text on error
      if (flavorTextTimeoutRef.current) {
        clearTimeout(flavorTextTimeoutRef.current);
      }
      setButtonText("Analyze Ingredients");
      
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
    
    // Clear any existing timeout
    if (flavorTextTimeoutRef.current) {
      clearTimeout(flavorTextTimeoutRef.current);
    }
    
    // Check if any product inputs are vague (don't clear previous vague warning yet)
    const vagueProducts = validProducts.filter(p => {
      const vagueCheck = isVagueInput(p.ingredients);
      return vagueCheck.isVague;
    });
    
    if (vagueProducts.length > 0) {
      const vagueCheck = isVagueInput(vagueProducts[0].ingredients);
      const suggestion1 = vagueCheck.suggestions[0] || "brand name";
      const suggestion2 = vagueCheck.suggestions[1] || "specific type";
      setAiInputError(`We recommend giving the AI a bit more data such as ${suggestion1} or ${suggestion2} to ensure accurate results, but we can roll with this for the time being`);
    } else {
      // Only clear if the new input is NOT vague
      setAiInputError(null);
    }
    
    // Set initial text
    setBatchButtonText("May take up to 2 minutes");
    
    // After 3-5 seconds, change to random flavor text
    const delay = Math.random() * 2000 + 3000; // 3000-5000ms
    flavorTextTimeoutRef.current = setTimeout(() => {
      const randomFlavor = flavorTexts[Math.floor(Math.random() * flavorTexts.length)];
      setBatchButtonText(randomFlavor);
    }, delay);
    
    try {
      const result = await postBatchProductsForAnalysis(validProducts);
      setIsBatchLoading(false);
      
      // Clear timeout and reset button text
      if (flavorTextTimeoutRef.current) {
        clearTimeout(flavorTextTimeoutRef.current);
      }
      setBatchButtonText("Analyze Batch");
      
      if (result.error) {
        // Check if it's a non-food item error
        if (result.error.includes("Non-food items detected") || result.error.toLowerCase().includes("non-food")) {
          setAiInputError("Input food item");
        } else {
          // For other errors, show in toast
          toast({ title: "Error", description: result.error, variant: "destructive" });
        }
      } else {
        // Don't clear vague input warning on success - let it persist
        // Only clear if it was a different type of error
        setBatchResults(result);
        
        // Save to history
        const historyItem: HistoryItem = {
          id: `history-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          input: validProducts.map(p => `${p.product}: ${p.ingredients}`).join(" | "),
          output: result,
          isBatch: true,
        };
        setHistory(prev => [historyItem, ...prev]);
        setSelectedHistoryId(historyItem.id);
      }
    } catch (e) {
      setIsBatchLoading(false);
      
      // Clear timeout and reset button text on error
      if (flavorTextTimeoutRef.current) {
        clearTimeout(flavorTextTimeoutRef.current);
      }
      setBatchButtonText("Analyze Batch");
      
      toast({ 
        title: "Error", 
        description: e instanceof Error ? e.message : "Unknown error", 
        variant: "destructive" 
      });
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
            <h1 className="text-2xl font-bold font-headline">CarcinogenScan AI</h1>
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
      <main className="flex-grow flex p-4 sm:p-6 lg:p-8 gap-6">
        {/* Left Sidebar - History Section */}
        <aside className="w-64 flex-shrink-0 hidden lg:block">
          <div className="sticky top-6">
            <div className="bg-card border rounded-lg p-3 shadow-sm flex flex-col max-h-[calc(100vh-3rem)]">
              <h3 className="text-base font-bold font-headline mb-3">History</h3>
              <div className="flex-1 overflow-y-auto space-y-2 min-h-0">
                {history.length === 0 ? (
                  <p className="text-xs text-muted-foreground">
                    Past analyses and model output will appear here.
                  </p>
                ) : (
                  history.map((item) => {
                    const isSelected = selectedHistoryId === item.id;
                    const timeStr = item.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    const inputPreview = item.input.length > 30 
                      ? item.input.substring(0, 30) + "..." 
                      : item.input;
                    
                    return (
                      <button
                        key={item.id}
                        onClick={() => handleHistorySelect(item)}
                        className={`w-full text-left p-2 rounded border transition-colors ${
                          isSelected 
                            ? "bg-primary/10 border-primary" 
                            : "bg-muted/50 border-border hover:bg-muted"
                        }`}
                      >
                        <div className="text-xs font-semibold mb-1">{timeStr}</div>
                        <div className="text-xs text-muted-foreground truncate">
                          {inputPreview}
                        </div>
                        {item.isBatch && (
                          <div className="text-xs text-primary mt-1">Batch</div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col items-center min-w-0">
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
                  {isLoading ? buttonText : "Analyze Ingredients"}
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
                {isBatchLoading ? batchButtonText : "Analyze Batch"}
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
        </div>

        {/* Right Sidebar - AI Input Section */}
        <aside className="w-64 flex-shrink-0 hidden lg:block">
          <div className="sticky top-6">
            <div className="bg-card border rounded-lg p-3 shadow-sm">
              <h3 className="text-base font-bold font-headline mb-3">AI Input</h3>
              <div className="min-h-[150px]">
                {aiInputError ? (
                  <div className="p-2 bg-destructive/10 border border-destructive/20 rounded text-xs text-destructive">
                    {aiInputError}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    AI error messages and feedback will appear here.
                  </p>
                )}
              </div>
            </div>
          </div>
        </aside>
      </main>
      <footer className="text-center p-4 text-xs text-muted-foreground bg-card border-t">
        <div className="flex flex-col items-center gap-2">
          <div>CarcinogenScan AI &copy; {new Date().getFullYear()}. All Rights Reserved. For informational purposes only. Not a substitute for professional medical advice.</div>
          <div className="text-xs text-muted-foreground">
            This site is protected by reCAPTCHA and the Google{" "}
            <a 
              href="https://policies.google.com/privacy" 
              target="_blank" 
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              Privacy Policy
            </a>
            {" "}and{" "}
            <a 
              href="https://policies.google.com/terms" 
              target="_blank" 
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              Terms of Service
            </a>
            {" "}apply.
          </div>
          <a
            href="https://www.instagram.com/carcinogenscanai/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors duration-200 group"
            aria-label="Follow us on Instagram"
          >
            <Instagram className="h-5 w-5 group-hover:scale-110 transition-transform duration-200" />
            <span className="text-sm">Find us on Insta!</span>
          </a>
        </div>
      </footer>
    </div>
  );
}
