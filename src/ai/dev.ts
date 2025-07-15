import { config } from 'dotenv';
config();

import '@/ai/flows/integrate-custom-chatgpt-model.ts';
import '@/ai/flows/formulate-prompt-for-carcinogen-risk-assessment.ts';