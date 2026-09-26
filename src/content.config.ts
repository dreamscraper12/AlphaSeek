import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const ai = z.object({
  used_for: z.array(z.string()),
  human: z.array(z.string()),
  ai_fair_value: z.number().optional(),
});

// A company note: the full section 14 schema. `type` may be omitted.
const companyNote = z.object({
  type: z.literal('company').default('company'),
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
  ai,
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
});

// A post: anything that isn't about a single holding (outlooks, letters,
// process). No instrument, price or fair value, but the AI disclosure is
// still required, as on every note.
const post = z.object({
  type: z.literal('post'),
  title: z.string(),
  published_at: z.coerce.date(),
  summary: z.string().optional(),
  ai,
});

const notes = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/notes' }),
  schema: z.union([companyNote, post]),
});

const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
  schema: z.object({
    title: z.string(),
  }),
});

export const collections = { notes, pages };
