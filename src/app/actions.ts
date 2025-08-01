"use server";

export async function getRagResponse(prompt: string): Promise<{ answer: string | null; error: string | null }> {
  if (!prompt.trim()) {
    return { answer: null, error: "Please enter a prompt." };
  }
  try {
    const response = await fetch("http://localhost:8000/rag", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: prompt, context: [] })
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return { answer: data.answer ?? null, error: null };
  } catch (e) {
    const errorMessage = e instanceof Error ? e.message : "An unknown error occurred.";
    return { answer: null, error: `An error occurred while contacting the AI model: ${errorMessage}` };
  }
}

export async function postIngredientsForAnalysis(ingredients: string): Promise<any> {
  try {
    console.log("Attempting to fetch from backend...");
    const response = await fetch("http://localhost:8000/ingredients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingredients })
    });
    
    console.log("Response status:", response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend error:", errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    
    const data = await response.json();
    console.log("Backend response:", data);
    return data;
  } catch (e) {
    console.error("Fetch error:", e);
    return { error: e instanceof Error ? e.message : "Unknown error" };
  }
}

export async function postBatchProductsForAnalysis(products: { product: string; ingredients: string }[]): Promise<any> {
  try {
    const response = await fetch("http://localhost:8000/ingredients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(products)
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (e) {
    return { error: e instanceof Error ? e.message : "Unknown error" };
  }
}

export async function checkBackendHealth(): Promise<any> {
  try {
    const response = await fetch("http://localhost:8000/health");
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (e) {
    return { error: e instanceof Error ? e.message : "Unknown error" };
  }
}
