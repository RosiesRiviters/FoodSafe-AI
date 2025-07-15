// src/ai/flows/formulate-prompt-for-carcinogen-risk-assessment.ts
'use server';

/**
 * @fileOverview Formulates a prompt for carcinogen risk assessment based on food input.
 *
 * - formulatePromptForCarcinogenRiskAssessment - A function that formulates the prompt for carcinogen risk assessment.
 * - FormulatePromptForCarcinogenRiskAssessmentInput - The input type for the formulatePromptForCarcinogenRiskAssessment function.
 * - FormulatePromptForCarcinogenRiskAssessmentOutput - The return type for the formulatePromptForCarcinogenRiskAssessment function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const FormulatePromptForCarcinogenRiskAssessmentInputSchema = z.object({
  foodInput: z.string().describe('The food items to be assessed for carcinogen risk.'),
});
export type FormulatePromptForCarcinogenRiskAssessmentInput = z.infer<
  typeof FormulatePromptForCarcinogenRiskAssessmentInputSchema
>;

const FormulatePromptForCarcinogenRiskAssessmentOutputSchema = z.object({
  prompt: z.string().describe('The formulated prompt for carcinogen risk assessment.'),
});
export type FormulatePromptForCarcinogenRiskAssessmentOutput = z.infer<
  typeof FormulatePromptForCarcinogenRiskAssessmentOutputSchema
>;

export async function formulatePromptForCarcinogenRiskAssessment(
  input: FormulatePromptForCarcinogenRiskAssessmentInput
): Promise<FormulatePromptForCarcinogenRiskAssessmentOutput> {
  return formulatePromptForCarcinogenRiskAssessmentFlow(input);
}

const formulatePrompt = ai.definePrompt({
  name: 'formulatePrompt',
  input: {schema: FormulatePromptForCarcinogenRiskAssessmentInputSchema},
  output: {schema: FormulatePromptForCarcinogenRiskAssessmentOutputSchema},
  prompt: `You are an AI assistant specializing in formulating prompts for a custom ChatGPT model that identifies the risk of carcinogens in food.

  Based on the user's food input, create a prompt that asks the model to assess the carcinogen risk associated with the food.

  Food Input: {{{foodInput}}}

  Formulated Prompt:`, // Ensure that the prompt is geared towards identifying carcinogen risks within the provided food input.
});

const formulatePromptForCarcinogenRiskAssessmentFlow = ai.defineFlow(
  {
    name: 'formulatePromptForCarcinogenRiskAssessmentFlow',
    inputSchema: FormulatePromptForCarcinogenRiskAssessmentInputSchema,
    outputSchema: FormulatePromptForCarcinogenRiskAssessmentOutputSchema,
  },
  async input => {
    const {output} = await formulatePrompt(input);
    return output!;
  }
);
