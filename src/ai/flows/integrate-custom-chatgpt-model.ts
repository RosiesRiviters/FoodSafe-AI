'use server';
/**
 * @fileOverview Carcinogen risk assessment using a custom-trained ChatGPT model.
 *
 * - assessCarcinogenRisk - A function that assesses the risk of carcinogens in food items.
 * - AssessCarcinogenRiskInput - The input type for the assessCarcinogenRisk function.
 * - AssessCarcinogenRiskOutput - The return type for the assessCarcinogenRisk function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AssessCarcinogenRiskInputSchema = z.object({
  foodItems: z
    .string()
    .describe('A comma separated list of food items to assess for carcinogen risk.'),
});
export type AssessCarcinogenRiskInput = z.infer<typeof AssessCarcinogenRiskInputSchema>;

const AssessCarcinogenRiskOutputSchema = z.object({
  riskAssessment: z
    .string()
    .describe('The risk assessment of carcinogens in the provided food items.'),
  explanation: z
    .string()
    .describe('An explanation of the risk assessment, including specific ingredients of concern.'),
  disclaimer: z
    .string()
    .describe('A disclaimer that this application does not provide medical advice.'),
});
export type AssessCarcinogenRiskOutput = z.infer<typeof AssessCarcinogenRiskOutputSchema>;

export async function assessCarcinogenRisk(
  input: AssessCarcinogenRiskInput
): Promise<AssessCarcinogenRiskOutput> {
  return assessCarcinogenRiskFlow(input);
}

const assessCarcinogenRiskPrompt = ai.definePrompt({
  name: 'assessCarcinogenRiskPrompt',
  input: {schema: AssessCarcinogenRiskInputSchema},
  output: {schema: AssessCarcinogenRiskOutputSchema},
  prompt: `You are an expert in food safety and carcinogens.

  Assess the risk of carcinogens in the following food items:
  {{foodItems}}

  Provide a risk assessment, an explanation of the risk, including specific ingredients of concern, and a disclaimer that this application does not provide medical advice.
  Respond in a JSON format.
  Make sure to include a disclaimer.`,
});

const assessCarcinogenRiskFlow = ai.defineFlow(
  {
    name: 'assessCarcinogenRiskFlow',
    inputSchema: AssessCarcinogenRiskInputSchema,
    outputSchema: AssessCarcinogenRiskOutputSchema,
  },
  async input => {
    const {output} = await assessCarcinogenRiskPrompt(input);
    return output!;
  }
);
