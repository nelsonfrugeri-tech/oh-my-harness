import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const chapters = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content" }),
  schema: z.object({
    order: z.number().int().positive(),
    id: z.string(),
    label: z.string(),
    title: z.string(),
    accent: z.string().optional(),
    lead: z.string(),
    diagram: z.enum([
      "portability",
      "architecture",
      "evidence",
      "knowledge",
      "engineering",
      "boundaries",
      "demo",
      "start",
    ]),
    note: z.string(),
    source: z.string(),
  }),
});

export const collections = { chapters };
