"use server";

import { assessCarcinogenRisk, type AssessCarcinogenRiskOutput } from "@/ai/flows/integrate-custom-chatgpt-model";

export async function getRiskAssessment(foodItems: string): Promise<{ data: AssessCarcinogenRiskOutput | null; error: string | null }> {
  if (!foodItems.trim()) {
    return { data: null, error: "Please enter some food items." };
  }
  
  try {
    const result = await assessCarcinogenRisk({ foodItems });
    return { data: result, error: null };
  } catch (e) {
    console.error(e);
    const errorMessage = e instanceof Error ? e.message : "An unknown error occurred.";
    return { data: null, error: `An error occurred while assessing the risk: ${errorMessage}. Please try again.` };
  }
}

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
    const response = await fetch("http://localhost:8000/ingredients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingredients })
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (e) {
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
