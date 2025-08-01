import { genkit } from 'genkit';
import { ollama } from 'genkitx-ollama';

export const ai = genkit({
  plugins: [
    ollama({
      models: [
        {
          name: 'gemma', // switched to Gemma model
          type: 'generate',
        },
      ],
      serverAddress: 'http://127.0.0.1:11434',
    }),
  ],
  model: 'ollama/gemma', // switched to Gemma model
});
