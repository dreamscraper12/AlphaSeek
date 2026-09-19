import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const notes = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/notes' }),
  schema: z.object({
    title: z.string(),
    instrument_id: z.string(),
    published_at: z.coerce.date(),
    status: z.enum(['open', 'exited', 'passed']),
    price_at_publication: z.number(),
    currency: z.string(),
    fair_value: z.number(),
    valuation_method: z.string(),
    key_assumptions: z.record(z.string(), z.union([z.number(), z.string()])).optional(),
    sensitivity: z
      .object({
        wacc: z.array(z.number()),
        terminal_growth: z.array(z.number()),
        values: z.array(z.array(z.number())),
      })
      .optional(),
    kill_criteria: z.array(z.string()).optional(),
    ai: z.object({
      used_for: z.array(z.string()),
      human: z.array(z.string()),
      ai_fair_value: z.number().optional(),
    }),
    model_file: z.string().optional(),
    updates: z
      .array(
        z.object({
          date: z.coerce.date(),
          fair_value: z.number(),
          summary: z.string(),
        }),
      )
      .optional(),
    exit: z
      .object({
        date: z.coerce.date(),
        reason: z.string(),
        kill_criteria_triggered: z.boolean(),
        lessons: z.string(),
      })
      .optional(),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
  schema: z.object({
    title: z.string(),
  }),
});

export const collections = { notes, pages };
